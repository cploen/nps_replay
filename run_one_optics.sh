#!/bin/bash

set -euo pipefail

RUN=$1

echo "Starting optics replay for run ${RUN}"
echo "Host: $(hostname)"
echo "Time: $(date)"
echo "PWD: $(pwd)"

cd /u/group/nps/cploen/nps_replay
 
source setup.sh

OUTDIR="/w/hallc-scshelf2102/nps/cploen/ROOTfiles/OPTICS/angular_sandbox/zero_offsets/"
mkdir -p "$OUTDIR"

hcana -q "SCRIPTS/NPS/OPTICS/replay_optics_coin_NPS_HMS.(${RUN}, -1,1,99)"

echo "Finished run ${RUN}"
echo "Time: $(date)"
