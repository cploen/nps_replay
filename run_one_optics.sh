#!/bin/bash

set -euo pipefail

RUN=$1

echo "Starting optics replay for run ${RUN}"
echo "Host: $(hostname)"
echo "Time: $(date)"
echo "PWD: $(pwd)"


source /etc/profile.d/modules.sh

module use /apps/modulefiles
module use /group/halla/modulefiles
module use /group/nps/modulefiles
module load nps_replay/5.28.24

cd /u/group/nps/cploen/nps_replay
echo "Git branch: $(git branch --show-current)"
echo "Git commit: $(git log -1 --oneline)"

source setup.sh

OUTDIR="/w/hallc-scshelf2102/nps/cploen/ROOTfiles/OPTICS/angular_sandbox/zero_offsets/"
mkdir -p "$OUTDIR"

hcana -l -b -q 'SCRIPTS/NPS/OPTICS/replay_optics_coin_NPS_HMS.C('"${RUN}"',-1,1,20)'

echo "Finished run ${RUN}"
echo "Time: $(date)"
