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
# Use the same environment setup as the existing hcswif wrapper.
source "$farm_setup"
cd "$scratch_dir"
command -v hcana
for ((segment=0; segment<=max_segment; segment++)); do
  [[ -s nps_coin_${run}.dat.${segment} ]]
done
mkdir -p ROOTfiles/OPTICS REPORT_OUTPUT/HMS
echo "Run $run, all segments 0 through $max_segment; all events; October 29 beam basis, constrained YTAR=0 refit, angular constants applied through hmsflags"
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
