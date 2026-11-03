#!/usr/bin/env bash
# One complete raw segment, in the SWIF job's private scratch directory.
set -eo pipefail
if [[ $# != 3 ]]; then
  echo 'Usage: elastic_swif_worker.sh RUN SEGMENT HCSWIF_SETUP' >&2
  exit 2
fi
run=$1
segment=$2
farm_setup=$3
scratch_dir=$PWD
[[ $run =~ ^[0-9]+$ && $segment =~ ^[0-9]+$ ]]
tar -xzf nps_replay.tar.gz
# Use the same environment setup as the existing hcswif wrapper.
source "$farm_setup"
cd "$scratch_dir"
command -v hcana
[[ -s nps_coin_${run}.dat.${segment} ]]
mkdir -p ROOTfiles/OPTICS REPORT_OUTPUT/HMS
echo "Run $run, segment $segment; all events; October 29 beam matrix, embedded offsets"
cat ELASTIC_REPLAY_PROVENANCE.json
hcana -l -b -q "SCRIPTS/NPS/OPTICS/replay_optics_coin_NPS_HMS.C($run,-1,1,$segment,$segment)"
shopt -s nullglob
roots=(ROOTfiles/OPTICS/*.root)
reports=(REPORT_OUTPUT/HMS/*.report)
(( ${#roots[@]} > 0 && ${#reports[@]} > 0 )) || {
  echo 'Replay did not produce the expected ROOT file and report.' >&2
  exit 5
}
./check_root ROOTfiles/OPTICS
echo "Completed run $run segment $segment"
