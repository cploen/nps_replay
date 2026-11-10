#!/usr/bin/env python3
"""Submit complete elastic or sieve runs to SWIF2, with all raw segments staged."""
import argparse
import datetime
import glob
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tarfile

CALIBRATION_FILE = 'config/hms_angular_delta_20261105/fit_manifest.json'
CALIBRATION = json.loads((Path(__file__).resolve().parents[1] / CALIBRATION_FILE).read_text())
MATRICES = {key: value['matrix_sha256'] for key, value in CALIBRATION['settings'].items()}
ANGULAR_OFFSETS_RAD = {key: {name: value['offsets'][name] for name in ('hphi_offset', 'htheta_offset')}
                       for key, value in CALIBRATION['settings'].items()}
DEFAULT_OUTPUT_ROOT = '/volatile/hallc/nps/cploen/ROOTfiles/nov05_angular_delta_matrix_flags_offsets_ytar0_refit_20261105'

SOURCE_MATRICES = {'5p878': '855aecc8205a17b8e42d9867f61b2da7c7eb6655b1af8628cb56e3cf82468772', '6p117': '067a0187901d08a00f62171f0d34a9e5932f85c077eabfee55da88a1fda41355', '6p667': 'd60928e0b0ac81347431e30fd5bb6355faed121b2f16d70ee9c90e8fd599b76d'}


def run_numbers(path):
    result = set()
    for line in Path(path).read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        if not re.fullmatch(r'[0-9]+', line):
            raise ValueError('Expected one run number per line: ' + line)
        result.add(int(line))
    if not result:
        raise ValueError('Empty run list')
    return sorted(result)


def raw_segments(runs, mss):
    result = []
    for run in runs:
        found = []
        for path in glob.glob(str(Path(mss) / f'nps_coin_{run}.dat.*')):
            suffix = path.rsplit('.', 1)[-1]
            if not suffix.isdecimal():
                continue
            match = re.search(r'\bsize\s*=\s*(\d+)', Path(path).read_text())
            if not match or int(match[1]) <= 0:
                raise ValueError('Missing positive MSS size: ' + path)
            found.append({'run': run, 'segment': int(suffix), 'bytes': int(match[1]), 'mss': path})
        if not found:
            raise ValueError(f'No MSS segments found for run {run}')
        if len({f['segment'] for f in found}) != len(found):
            raise ValueError(f'Duplicate segment number for run {run}')
        available = sorted(f['segment'] for f in found)
        if available != list(range(available[-1] + 1)):
            raise ValueError(f'Run {run} requires contiguous segments starting at 0; found {available}')
        result.extend(sorted(found, key=lambda f: f['segment']))
    return result


def configuration(repo, runs, calibration=CALIBRATION):
    for setting, item in calibration['settings'].items():
        expected = item['matrix_sha256']
        matrix = repo / item['matrix']
        if hashlib.sha256(matrix.read_bytes()).hexdigest() != expected:
            raise ValueError('Unexpected matrix: ' + str(matrix))
        for line in matrix.read_text().splitlines():
            fields = line.split()
            if len(fields) == 5 and fields[-1] == '00000':
                raise ValueError('Active 00000 row would duplicate flags offsets: ' + str(matrix))
        text = (repo / item['flags']).read_text()
        expected_flags = item['flags_sha256']
        if hashlib.sha256(text.encode()).hexdigest() != expected_flags:
            raise ValueError('Unexpected HMS flags for ' + setting)
        for name in ['htheta_offset', 'hphi_offset', 'hdelta_offset']:
            values = re.findall(rf'^\s*{name}\s*=\s*([^;\n]+)', text, re.M)
            if len(values) != 1 or float(values[0]) != item['offsets'][name]:
                raise ValueError('Unexpected fitted target offset: ' + name)
        if calibration.get('all_offsets_zero'):
            for name in ('htheta_offset','hphi_offset','hdelta_offset','hpcentral_offset',
                         'hthetacentral_offset','h_oopcentral_offset','hmomentum_factor'):
                values = re.findall(rf'^\s*{name}\s*=\s*([^;\n]+)', text, re.M)
                if len(values) != 1 or float(values[0]) != 0:
                    raise ValueError('Zero-offset test has a nonzero or missing flag: ' + name)
    kin = (repo / 'DBASE/NPS/standard_coin.kinematics').read_text()
    block = re.search(r'(?ms)^1253\s*\n(.*?)(?=^\d+\s*(?:-\s*\d+)?\s*$|\Z)', kin)
    angle = re.search(r'^htheta_lab\s*=\s*([^;\s]+)', block[1], re.M) if block else None
    if not angle or float(angle[1]) != -22.120:
        raise ValueError('Run 1253 must retain htheta_lab = -22.120 degrees')
    # Resolve the run-range optics assignments, in their file order.
    database = (repo / 'DBASE/NPS/standard_coin.database').read_text()
    selected = {run: None for run in runs}
    interval = (0, 10**12)
    for line in database.splitlines():
        line = line.split(';', 1)[0].strip()
        match = re.fullmatch(r'(\d+)\s*-\s*(\d+)', line)
        if match:
            interval = tuple(map(int, match.groups()))
        match = re.match(r'g_ctp_optics_filename\s*=\s*"([^"]+)"', line)
        if match:
            for run in runs:
                if interval[0] <= run <= interval[1]:
                    selected[run] = match[1]
    optics_paths = {item.get('optics',f'PARAM/HMS/GEN/hcana_{setting}.param'):setting
                    for setting,item in calibration['settings'].items()}
    for run, path in selected.items():
        if path not in optics_paths:
            raise ValueError(f'Run {run} selects {path}, not a configured calibration setting')
        setting = optics_paths[path]
        item = calibration['settings'][setting]
        if 'expected_runs' in item and run not in item['expected_runs']:
            raise ValueError(f'Run {run} resolves to the wrong momentum setting: {setting}')
        text = (repo / path).read_text()
        if (f'#include "{item["flags"]}"' not in text or
                f"'{item['matrix']}'" not in text):
            raise ValueError('Unexpected optics configuration: ' + path)
        selected[run] = setting
    return selected


def main():
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runlist', help='one run number per line')
    parser.add_argument('--calibration',default=CALIBRATION_FILE,help='Committed calibration manifest relative to this checkout')
    parser.add_argument('--sample', choices=['elastic', 'sieve'], default='elastic')
    parser.add_argument('--setup', default=str(repo / 'jobs/setup_elastic_farm.sh'))
    parser.add_argument('--mss', default='/mss/hallc/c-nps/raw')
    parser.add_argument('--output', help='override the sample-specific volatile output directory')
    parser.add_argument('--workflow', help='override the sample-specific workflow name')
    parser.add_argument('--account', default='hallc')
    parser.add_argument('--partition', default='production')
    parser.add_argument('--constraint', default='el9')
    parser.add_argument('--ram', default='3GB')
    parser.add_argument('--time', default='24h')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare', action='store_true', help='freeze runtime files and write submission commands without queuing jobs')
    mode.add_argument('--submit', action='store_true', help='freeze inputs, create complete-run jobs and start the workflow')
    args = parser.parse_args()
    calibration_file = str(Path(args.calibration))
    calibration = json.loads((repo/calibration_file).read_text())
    matrices = {key:item['matrix_sha256'] for key,item in calibration['settings'].items()}
    angular_offsets = {key:{name:item['offsets'][name] for name in ('hphi_offset','htheta_offset')}
                       for key,item in calibration['settings'].items()}
    sample_dir = 'ELASTIC' if args.sample == 'elastic' else 'OPTICS/SIEVE'
    if args.output is None:
        args.output = f'{DEFAULT_OUTPUT_ROOT}/{sample_dir}'
    if args.workflow is None:
        args.workflow = f'hms_{args.sample}_angdelta_ytar0_fullrun_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    runs = run_numbers(args.runlist)
    segments = raw_segments(runs, args.mss)
    run_inputs = {run: [item for item in segments if item['run'] == run] for run in runs}
    settings = configuration(repo, runs, calibration)
    if not Path(args.setup).is_file():
        raise ValueError('Missing hcswif environment setup: ' + args.setup)
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.workflow):
        raise ValueError('Workflow name may contain only letters, digits, underscores and hyphens')
    print(f'{len(runs)} complete-run jobs, {len(segments)} raw segments, all events (-1)')
    for setting in matrices:
        print(setting, 'runs:', ' '.join(str(r) for r in runs if settings[r] == setting))
    output = Path(args.output).resolve() / args.workflow
    print('Output:', output)
    if not (args.prepare or args.submit):
        print('Plan only. Use --prepare to freeze inputs or --submit to prepare and queue complete runs.')
        return
    if args.submit and not shutil.which('swif2'):
        raise ValueError('swif2 is unavailable; run this command on ifarm')
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--'], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
    output.mkdir(parents=True, exist_ok=False)
    provenance = output / 'provenance'
    provenance.mkdir()
    log_dir = Path('/farm_out') / os.environ['USER'] / args.workflow
    log_dir.mkdir(parents=True, exist_ok=True)
    runtime_paths = [calibration_file, 'DBASE/NPS/standard_coin.database', 'DBASE/NPS/standard_coin.kinematics']
    for setting,item in calibration['settings'].items():
        runtime_paths.extend([item['matrix'], item['flags'],
                              item.get('optics',f'PARAM/HMS/GEN/hcana_{setting}.param')])
    runtime_hashes = {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in runtime_paths}
    metadata = {'sample': args.sample, 'commit': commit, 'matrix_sha256': matrices, 'external_angular_offsets_rad': angular_offsets,
                'external_delta_offsets_fraction': {s: v['offsets']['hdelta_offset'] for s, v in calibration['settings'].items()},
                'calibration_file': calibration_file, 'calibration': calibration,
                'runtime_file_sha256': runtime_hashes,
                'source_matrix_sha256': calibration.get('source_matrix_sha256',SOURCE_MATRICES),
                'angular_offset_convention': calibration.get('zero_order_convention','hmsflags; all 00000 values are header comments only'),
                'delta_offset_convention': 'hdelta_offset is fractional delta, added before H.gtr.dp is multiplied by 100',
                'matrix_source_repository': 'cploen/hallc_spectrometer_angular_optics',
                'matrix_source_commit': 'd7c8311763adb843698ca8028f24064f9527f64a',
                'matrix_source_directory': calibration.get('matrix_source_directory','07_diagnostics/ytar_zero_refit_20261103'),
                'ytar_constant_fixed': 0,
                'job_granularity': 'complete_run',
                'run_segments': {run: [item['segment'] for item in items] for run, items in run_inputs.items()},
                'run_settings': settings, 'segments': segments, 'events': -1,
                'setup_path': str(Path(args.setup).resolve()),
                'setup_sha256': hashlib.sha256(Path(args.setup).read_bytes()).hexdigest(),
                'kinematics_sha256': hashlib.sha256((repo / 'DBASE/NPS/standard_coin.kinematics').read_bytes()).hexdigest()}
    metadata_bytes = (json.dumps(metadata, indent=2) + '\n').encode()
    (provenance / 'manifest.json').write_bytes(metadata_bytes)
    shutil.copyfile(args.runlist, provenance / f'{args.sample}_runs.txt')
    worker = provenance / 'elastic_swif_worker.sh'
    shutil.copyfile(repo / 'jobs/elastic_swif_worker.sh', worker)
    farm_setup = provenance / 'elastic_farm_setup.sh'
    shutil.copyfile(args.setup, farm_setup)
    archive = provenance / 'nps_replay.tar'
    with archive.open('wb') as stream:
        subprocess.run(['git', 'archive', '--format=tar', commit], cwd=repo, stdout=stream, check=True)
    with tarfile.open(archive, 'a') as tar:
        item = tarfile.TarInfo('ELASTIC_REPLAY_PROVENANCE.json')
        item.size = len(metadata_bytes)
        tar.addfile(item, io.BytesIO(metadata_bytes))
    subprocess.run(['gzip', str(archive)], check=True)
    archive = Path(str(archive) + '.gz')
    # Copy the actual committed runtime inputs out of the job snapshot, not live files.
    with tarfile.open(archive, 'r:gz') as tar:
        for name, expected in runtime_hashes.items():
            raw = tar.extractfile(name).read()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError('Committed snapshot differs from runtime input: ' + name)
            dest = provenance / 'runtime_config' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
    (provenance / 'snapshot_sha256.txt').write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + '  nps_replay.tar.gz\n')
    commands = []
    for run, items in run_inputs.items():
        max_segment = items[-1]['segment']
        raw_bytes = sum(item['bytes'] for item in items)
        destination = output / settings[run] / f'run_{run}'
        for directory in ['rootfiles', 'reports']:
            (destination / directory).mkdir(parents=True)
        raw_inputs = []
        for item in items:
            raw_inputs.extend(['-input', f'nps_coin_{run}.dat.{item["segment"]}', 'mss:' + item['mss']])
        command = ['swif2', 'add-job', args.workflow, '-name', f'{args.sample}_{run}',
                   '-account', args.account, '-partition', args.partition, '-cores', '1',
                   '-constraint', args.constraint,
                   '-ram', args.ram, '-time', args.time,
                   '-disk-scratch', str(max(50_000_000_000, raw_bytes * 4)),
                   '-stdout', str(log_dir / '@job_name@-@attempt_id@.out'),
                   '-stderr', str(log_dir / '@job_name@-@attempt_id@.err'),
                   '-input', 'nps_replay.tar.gz', 'file:' + str(archive),
                   '-input', 'elastic_swif_worker.sh', 'file:' + str(worker),
                   '-input', 'elastic_farm_setup.sh', 'file:' + str(farm_setup)] + raw_inputs + [
                   '-output', 'match:ROOTfiles/OPTICS/*.root', 'file:' + str(destination / 'rootfiles'),
                   '-output', 'match:REPORT_OUTPUT/HMS/*.report', 'file:' + str(destination / 'reports'),
                   '/bin/bash', 'elastic_swif_worker.sh', str(run), str(max_segment), './elastic_farm_setup.sh']
        commands.append(command)
    (provenance / 'swif_commands.sh').write_text('\n'.join(' '.join(shlex.quote(x) for x in c) for c in commands) + '\n')
    submit_script = provenance / 'submit_prepared.sh'
    submit_script.write_text('#!/usr/bin/env bash\nset -euo pipefail\n' +
        shlex.join(['swif2', 'create', args.workflow]) + '\n' +
        '\n'.join(shlex.join(c) for c in commands) + '\n' +
        shlex.join(['swif2', 'run', args.workflow]) + '\n')
    submit_script.chmod(0o755)
    if args.prepare:
        print('Prepared immutable runtime snapshot; no jobs queued.')
        print('Runtime configuration copies:', provenance / 'runtime_config')
        print('Submit the saved snapshot: bash', submit_script)
        return
    subprocess.run(['swif2', 'create', args.workflow], check=True)
    for command in commands:
        subprocess.run(command, check=True)
    subprocess.run(['swif2', 'run', args.workflow], check=True)
    print('Started all complete-run jobs:', args.workflow)
    print('Monitor: swif2 status', args.workflow, '-jobs')
    print('Output:', output)


if __name__ == '__main__':
    main()
