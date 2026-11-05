#!/usr/bin/env python3
"""Prepare frozen sieve and elastic workflows for the November 5 calibration."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from submit_elastic_swif import run_numbers


def main():
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default=str(repo / 'config/hms_angular_delta_20261105/replay_campaign.json'))
    parser.add_argument('--output-root', help='override the shared volatile campaign parent')
    parser.add_argument('--mss', default='/mss/hallc/c-nps/raw')
    parser.add_argument('--setup', help='override the existing farm setup script')
    parser.add_argument('--workflow-suffix', default='', help='append a suffix when preparing a new campaign attempt')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--plan', action='store_true', help='show raw segment coverage without creating snapshots')
    modes.add_argument('--submit', action='store_true', help='prepare and start both workflows; default is prepare only')
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    parent = args.output_root or config['output_root']
    for sample in ('sieve', 'elastic'):
        item = config['samples'][sample]
        runlist = repo / item['runlist']
        if run_numbers(runlist) != sorted(item['expected_runs']):
            raise ValueError('Run list differs from the frozen campaign: ' + sample)
        workflow = item['workflow'] + ('_' + args.workflow_suffix if args.workflow_suffix else '')
        command = [sys.executable, str(repo / 'jobs/submit_elastic_swif.py'), str(runlist),
                   '--sample', sample, '--mss', args.mss,
                   '--output', str(Path(parent) / item['subdirectory']), '--workflow', workflow]
        if args.setup:
            command += ['--setup', args.setup]
        if args.submit:
            command.append('--submit')
        elif not args.plan:
            command.append('--prepare')
        print('Campaign sample:', sample, flush=True)
        subprocess.run(command, cwd=repo, check=True)


if __name__ == '__main__':
    main()
