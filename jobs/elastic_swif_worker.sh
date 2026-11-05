#!/usr/bin/env bash
# One complete run, including segment 0, in the job's private scratch directory.
set -eo pipefail
if [[ $# != 3 ]]; then
  echo 'Usage: elastic_swif_worker.sh RUN MAX_SEGMENT HCSWIF_SETUP' >&2
  exit 2
fi
run=$1
max_segment=$2
farm_setup=$3
scratch_dir=$PWD
[[ $run =~ ^[0-9]+$ && $max_segment =~ ^[0-9]+$ ]]
tar -xzf nps_replay.tar.gz
python3 - <<'PY'
import hashlib, json
from pathlib import Path
meta = json.loads(Path('ELASTIC_REPLAY_PROVENANCE.json').read_text())
for name, expected in meta['runtime_file_sha256'].items():
    if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
        raise SystemExit('Runtime configuration checksum mismatch: ' + name)
if hashlib.sha256(Path('elastic_farm_setup.sh').read_bytes()).hexdigest() != meta['setup_sha256']:
    raise SystemExit('Farm setup checksum mismatch')
print('Verified frozen matrices, flags, optics parameters and run database')
PY
# Use the same environment setup as the existing hcswif wrapper.
source "$farm_setup"
cd "$scratch_dir"
command -v hcana
for ((segment=0; segment<=max_segment; segment++)); do
  [[ -s nps_coin_${run}.dat.${segment} ]]
done
mkdir -p ROOTfiles/OPTICS REPORT_OUTPUT/HMS
echo "Run $run, all segments 0 through $max_segment; all events; angular plus delta calibration 2026-11-05, YTAR zero-order fixed, constants applied once through hmsflags"
cat ELASTIC_REPLAY_PROVENANCE.json
hcana -l -b -q "SCRIPTS/NPS/OPTICS/replay_optics_coin_NPS_HMS.C($run,-1,1,$max_segment,0)"
shopt -s nullglob
roots=(ROOTfiles/OPTICS/*.root)
reports=(REPORT_OUTPUT/HMS/*.report)
(( ${#roots[@]} > 0 && ${#reports[@]} > 0 )) || {
  echo 'Replay did not produce the expected ROOT file and report.' >&2
  exit 5
}
./check_root ROOTfiles/OPTICS
echo "Completed run $run, segments 0 through $max_segment"
