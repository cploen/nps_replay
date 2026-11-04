#!/usr/bin/env python3
"""Submit every MSS segment of an explicit elastic run list to SWIF2."""
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

MATRICES = {
    '5p878': '855aecc8205a17b8e42d9867f61b2da7c7eb6655b1af8628cb56e3cf82468772',
    '6p117': '067a0187901d08a00f62171f0d34a9e5932f85c077eabfee55da88a1fda41355',
    '6p667': 'd60928e0b0ac81347431e30fd5bb6355faed121b2f16d70ee9c90e8fd599b76d',
}


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
        raise ValueError('Empty elastic run list')
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
        result.extend(sorted(found, key=lambda f: f['segment']))
    return result


def configuration(repo, runs):
    for setting, expected in MATRICES.items():
        matrix = repo / f'DATFILES/nps_hms_optics_{setting}_ang.dat'
        if hashlib.sha256(matrix.read_bytes()).hexdigest() != expected:
            raise ValueError('Unexpected matrix: ' + str(matrix))
        text = (repo / f'PARAM/HMS/GEN/hmsflags_{setting}.param').read_text()
        for name in ['htheta_offset', 'hphi_offset']:
            values = re.findall(rf'^\s*{name}\s*=\s*([^;\n]+)', text, re.M)
            if len(values) != 1 or float(values[0]) != 0.:
                raise ValueError('Expected zero external offset: ' + name)
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
    for run, path in selected.items():
        match = re.fullmatch(r'PARAM/HMS/GEN/hcana_(5p878|6p117|6p667)\.param', path or '')
        if not match:
            raise ValueError(f'Run {run} selects {path}, not one of the three final-fit settings')
        setting = match[1]
        text = (repo / path).read_text()
        if (f'#include "PARAM/HMS/GEN/hmsflags_{setting}.param"' not in text or
                f"'DATFILES/nps_hms_optics_{setting}_ang.dat'" not in text):
            raise ValueError('Unexpected optics configuration: ' + path)
        selected[run] = setting
    return selected


def main():
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runlist', help='one elastic run number per line')
    parser.add_argument('--setup', default=str(repo / 'jobs/setup_elastic_farm.sh'))
    parser.add_argument('--mss', default='/mss/hallc/c-nps/raw')
    parser.add_argument('--output', default='/volatile/hallc/nps/cploen/ROOTfiles/ELASTIC/oct29_beam_search_matrix_embedded_offsets_ytar0_refit_20261103')
    parser.add_argument('--workflow', default='hms_elastic_oct29_ytar0_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    parser.add_argument('--account', default='hallc')
    parser.add_argument('--partition', default='production')
    parser.add_argument('--constraint', default='el9')
    parser.add_argument('--ram', default='3GB')
    parser.add_argument('--time', default='24h')
    parser.add_argument('--submit', action='store_true', help='create, add every segment, and start the complete workflow')
    args = parser.parse_args()
    runs = run_numbers(args.runlist)
    segments = raw_segments(runs, args.mss)
    settings = configuration(repo, runs)
    if not Path(args.setup).is_file():
        raise ValueError('Missing hcswif environment setup: ' + args.setup)
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.workflow):
        raise ValueError('Workflow name may contain only letters, digits, underscores and hyphens')
    print(f'{len(runs)} runs, {len(segments)} segment jobs, all events (-1)')
    for setting in MATRICES:
        print(setting, 'runs:', ' '.join(str(r) for r in runs if settings[r] == setting))
    output = Path(args.output).resolve() / args.workflow
    print('Output:', output)
    if not args.submit:
        print('Plan only. Add --submit to queue every segment and start the workflow.')
        return
    if not shutil.which('swif2'):
        raise ValueError('swif2 is unavailable; run this command on ifarm')
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--'], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
    output.mkdir(parents=True, exist_ok=False)
    provenance = output / 'provenance'
    provenance.mkdir()
    log_dir = Path('/farm_out') / os.environ['USER'] / args.workflow
    log_dir.mkdir(parents=True, exist_ok=True)
    metadata = {'commit': commit, 'matrix_sha256': MATRICES, 'external_angular_offsets': 0,
                'matrix_source_repository': 'cploen/hallc_spectrometer_angular_optics',
                'matrix_source_commit': 'd7c8311763adb843698ca8028f24064f9527f64a',
                'matrix_source_directory': '07_diagnostics/ytar_zero_refit_20261103',
                'ytar_constant_fixed': 0,
                'run_settings': settings, 'segments': segments, 'events': -1,
                'setup_path': str(Path(args.setup).resolve()),
                'setup_sha256': hashlib.sha256(Path(args.setup).read_bytes()).hexdigest(),
                'kinematics_sha256': hashlib.sha256((repo / 'DBASE/NPS/standard_coin.kinematics').read_bytes()).hexdigest()}
    metadata_bytes = (json.dumps(metadata, indent=2) + '\n').encode()
    (provenance / 'manifest.json').write_bytes(metadata_bytes)
    shutil.copyfile(args.runlist, provenance / 'elastic_runs.txt')
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
    commands = []
    for item in segments:
        run, seg = item['run'], item['segment']
        destination = output / settings[run] / f'run_{run}' / f'seg_{seg}'
        for directory in ['rootfiles', 'reports']:
            (destination / directory).mkdir(parents=True)
        command = ['swif2', 'add-job', args.workflow, '-name', f'elastic_{run}_seg{seg}',
                   '-account', args.account, '-partition', args.partition, '-cores', '1',
                   '-constraint', args.constraint,
                   '-ram', args.ram, '-time', args.time,
                   '-disk-scratch', str(max(50_000_000_000, item['bytes'] * 4)),
                   '-stdout', str(log_dir / '@job_name@-@attempt_id@.out'),
                   '-stderr', str(log_dir / '@job_name@-@attempt_id@.err'),
                   '-input', 'nps_replay.tar.gz', 'file:' + str(archive),
                   '-input', 'elastic_swif_worker.sh', 'file:' + str(worker),
                   '-input', 'elastic_farm_setup.sh', 'file:' + str(farm_setup),
                   '-input', f'nps_coin_{run}.dat.{seg}', 'mss:' + item['mss'],
                   '-output', 'match:ROOTfiles/OPTICS/*.root', 'file:' + str(destination / 'rootfiles'),
                   '-output', 'match:REPORT_OUTPUT/HMS/*.report', 'file:' + str(destination / 'reports'),
                   '/bin/bash', 'elastic_swif_worker.sh', str(run), str(seg), './elastic_farm_setup.sh']
        commands.append(command)
    (provenance / 'swif_commands.sh').write_text('\n'.join(' '.join(shlex.quote(x) for x in c) for c in commands) + '\n')
    subprocess.run(['swif2', 'create', args.workflow], check=True)
    for command in commands:
        subprocess.run(command, check=True)
    subprocess.run(['swif2', 'run', args.workflow], check=True)
    print('Started all segment jobs:', args.workflow)
    print('Monitor: swif2 status', args.workflow, '-jobs')
    print('Output:', output)


if __name__ == '__main__':
    main()
