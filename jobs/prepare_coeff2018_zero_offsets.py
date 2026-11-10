#!/usr/bin/env python3
"""Prepare the updated 2018 Beam matrix, zero flags and four-setting replay manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from submit_elastic_swif import configuration, run_numbers

RUNS = {
    '4p637':[2184,2185,2186,2187],
    '5p878':[1711,1712,1713,1717,1718,1720,5168,5169,5170,5171,7008],
    '6p117':[1243,1245,1246,1248,1960,1961,1962,1964,1965,1966,1967,5165,5166,5167],
    '6p667':[1540,1544,5156,5157,5158,5159,5160,5161,5162,5163,5164,6981,6982,6983,6984,6985],
}
CONFIG = Path('config/coeff2018_new_zero_offsets_20261110')
MATRIX = 'DATFILES/hms_recon_coeff2018_new_zero_offsets.dat'
ZERO_FLAGS = ('hdelta_offset','htheta_offset','hphi_offset','hpcentral_offset',
              'hthetacentral_offset','h_oopcentral_offset','hmomentum_factor')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(repo, source, beam_manifest):
    dest = repo/CONFIG
    if dest.exists():
        raise FileExistsError(f'Already prepared: {dest}')
    beam = json.loads(beam_manifest.read_text())
    if beam.get('schema') != 'beam_v1' or beam.get('status') != 'complete':
        raise ValueError('Requires a complete frozen Beam result')
    if sha(source) != beam['outputs']['matrices/beam.dat']:
        raise ValueError('Source is not the frozen final Beam matrix')
    if source.resolve() != (beam_manifest.parent/'matrices/beam.dat').resolve():
        raise ValueError('Source and Beam manifest must come from the same result')
    lines = source.read_text().splitlines(True)
    rows = [line for line in lines if re.fullmatch(r'\d{5}',line.split()[-1] if line.split() else '')
            and len(line.split()) == 5]
    codes = [line.split()[-1] for line in rows]
    if len(codes) != len(set(codes)) or '00000' not in codes:
        raise ValueError('Missing or duplicate transport terms')
    removed = next(line for line in rows if line.split()[-1]=='00000')
    new = '! Updated 2018 Beam replay test: complete 00000 row removed; zero HMS flag offsets.\n'+''.join(line for line in lines if line != removed)
    text_rows = [line.split() for line in new.splitlines() if len(line.split())==5 and re.fullmatch(r'\d{5}',line.split()[-1])]
    if len(text_rows) != len(rows)-1 or any(fields[-1]=='00000' for fields in text_rows):
        raise ValueError('Zero-order removal failed')
    original = {line.split()[-1]:line for line in rows if line!=removed}
    if any(original[fields[-1]].split()!=fields for fields in text_rows):
        raise ValueError('Nonconstant coefficients changed')
    old_runs = set(run_numbers(repo/'jobs/sieve_oct29_runs.txt'))
    if old_runs != set(sum((RUNS[s] for s in ('5p878','6p117','6p667')), [])):
        raise ValueError('Existing physical-run list changed; inspect before preparing')
    target_flags, target_optics = {}, {}
    for setting in RUNS:
        template = setting if setting!='4p637' else 'fa22'
        optics = (repo/f'PARAM/HMS/GEN/hcana_{template}.param').read_text()
        includes = re.findall(r'^#include "(PARAM/HMS/GEN/hmsflags[^\"]*\.param)"',optics,re.M)
        if len(includes) != 1:
            raise ValueError(f'{template}: ambiguous existing flags include')
        flags = (repo/includes[0]).read_text()
        for flag in ZERO_FLAGS:
            flags,n = re.subn(rf'(?m)^\s*{flag}\s*=.*$',f'  {flag} = 0.0 ; zero-offset 2018-matrix replay test',flags)
            if n != 1:
                raise ValueError(f'{template}: missing or duplicate {flag}')
        flags = '\n'.join(line for line in flags.splitlines() if not line.startswith('; Angular plus delta calibration')
                          and 'All zero-order values are applied here once' not in line
                          and 'YTAR zero-order term held fixed' not in line
                          and 'Angular refit 2026-11-03' not in line)+'\n'
        flags = '; 2018 Beam replay test: every external reconstruction offset is zero.\n'+flags
        optics,n = re.subn(r'#include "PARAM/HMS/GEN/hmsflags_[^"]+\.param"',
                          f'#include "PARAM/HMS/GEN/hmsflags_{setting}.param"',optics)
        if n != 1:
            raise ValueError(f'{template}: ambiguous flags include')
        optics,n = re.subn(r'(?m)^\s*h_recon_coeff_filename\s*=.*$',
                          f"h_recon_coeff_filename = '{MATRIX}' ; updated 2018 matrix, zero offsets",optics)
        if n != 1:
            raise ValueError(f'{template}: ambiguous coefficient assignment')
        target_flags[setting],target_optics[setting] = flags,optics
    # Append only the missing fourth-setting optics override; detector calibrations stay unchanged.
    database = repo/'DBASE/NPS/standard_coin.database'
    addition = '\n; Updated 2018 matrix test: 4.637 GeV sieve runs\n2184 - 2187\ng_ctp_optics_filename = "PARAM/HMS/GEN/hcana_4p637.param"\n'
    dest.mkdir(parents=True)
    (repo/MATRIX).write_text(new)
    record = dict(schema='coeff2018_new_zero_offsets_v1',all_offsets_zero=True,
                  zero_order_convention='Complete active 00000 row removed; every external HMS reconstruction offset is zero',
                  source_matrix_sha256={s:sha(source) for s in RUNS},
                  source_beam_manifest_sha256=sha(beam_manifest),source_beam_manifest=str(beam_manifest.resolve()),
                  matrix_source_directory=str(beam_manifest.parent.resolve()),source_ytar_intercept_was_free=True,
                  removed_zero_order_row=removed.strip(),settings={})
    for setting in RUNS:
        flags = f'PARAM/HMS/GEN/hmsflags_{setting}.param'
        optics = f'PARAM/HMS/GEN/hcana_{setting}.param'
        (repo/flags).write_text(target_flags[setting])
        (repo/optics).write_text(target_optics[setting])
        record['settings'][setting] = dict(matrix=MATRIX,matrix_sha256=sha(repo/MATRIX),
                flags=flags,flags_sha256=sha(repo/flags),optics=optics,
                expected_runs=RUNS[setting],offsets={flag:0. for flag in ZERO_FLAGS})
    database.write_text(database.read_text()+addition)
    all_runs = sorted(sum(RUNS.values(), []))
    if len(all_runs) != len(set(all_runs)) or len(all_runs) != 45:
        raise ValueError('Expected 45 distinct physical runs')
    actual = configuration(repo,all_runs,record)
    if actual != {run:s for s,runs in RUNS.items() for run in runs}:
        raise ValueError('Run database resolves to an unexpected setting')
    matrix_hashes = {item['matrix_sha256'] for item in record['settings'].values()}
    if len(matrix_hashes) != 1:
        raise ValueError('All four settings must use exactly the same updated matrix')
    (dest/'fit_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    (dest/'sieve_runs.txt').write_text('\n'.join(map(str,all_runs))+'\n')
    (dest/'run_matrix_assignments.tsv').write_text('run\tsetting\toptics\tmatrix\tmatrix_sha256\tflags\tflags_sha256\n'+''.join(
        f'{run}\t{s}\t'+ '\t'.join(record['settings'][s][key] for key in ('optics','matrix','matrix_sha256','flags','flags_sha256'))+'\n'
        for run,s in sorted(actual.items())))
    print(f'Prepared {len(all_runs)} runs; every setting resolves to {MATRIX}',flush=True)
    print('Updated matrix SHA256:',sha(repo/MATRIX),flush=True)
    print('Calibration:',CONFIG/'fit_manifest.json',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix',type=Path,required=True)
    parser.add_argument('--beam-manifest',type=Path,required=True)
    args = parser.parse_args()
    prepare(Path(__file__).resolve().parents[1],args.matrix,args.beam_manifest)
