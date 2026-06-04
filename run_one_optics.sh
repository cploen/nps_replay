#!/bin/bash

set -euxo pipefail

RUN=$1
MAXSEG="${2:-20}"

echo "Starting optics replay for run ${RUN}"
echo "Max segment: ${MAXSEG}"
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

mkdir -p volatile/hallc/nps/cploen/ROOTfiles/OPTICS/angular_sandbox/delta_opt/newfit_6p667_20260526_1226_no_offsets/rootfiles/
 
hcana -l -b -q 'SCRIPTS/NPS/OPTICS/replay_optics_coin_NPS_HMS.C('"${RUN}"',-1,1,'"${MAXSEG}"')'

echo "Finished run ${RUN}"
echo "Time: $(date)"
