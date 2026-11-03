#!/usr/bin/env bash
# Environment used by the saved angular-sandbox run_one_optics.sh.
if [[ -r /etc/profile.d/modules.sh ]]; then
  source /etc/profile.d/modules.sh
elif [[ -r /apps/modules/5.2.0/init/profile.sh ]]; then
  source /apps/modules/5.2.0/init/profile.sh
else
  echo 'Cannot find the farm environment-modules initialization script.' >&2
  return 1
fi
module use /apps/modulefiles
module use /group/halla/modulefiles
module use /group/nps/modulefiles
module load nps_replay/5.28.24
source ./setup.sh
module list
