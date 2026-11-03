# Elastic replay with the October 29 angular matrices

Use `submit_elastic_swif.py` on ifarm with an explicit text file containing
one elastic run number per line. Blank lines and `#` comments are allowed.
Every available numeric segment under `/mss/hallc/c-nps/raw` is queued in
one SWIF2 workflow. All events are replayed (`-1`), with one job per segment.

```bash
python3 jobs/submit_elastic_swif.py /absolute/path/elastic_runs.txt --submit
```

The worker uses the existing `SCRIPTS/NPS/OPTICS/replay_optics_coin_NPS_HMS.C`
without changing its physics or output definitions. Each job gets a separate
scratch directory. It reads its staged raw segment from `.` and writes to
`ROOTfiles/OPTICS` and `REPORT_OUTPUT/HMS`. ROOT files are checked there with
the existing `check_root` program before SWIF copies outputs to volatile.

The output hierarchy is:

```text
/volatile/hallc/nps/cploen/ROOTfiles/ELASTIC/
  oct29_beam_search_matrix_embedded_offsets/WORKFLOW/
    5p878/run_RUN/seg_SEG/rootfiles/*.root
    5p878/run_RUN/seg_SEG/reports/*.report
    6p117/...
    6p667/...
    provenance/
```

Keeping each segment separate prevents the unchanged optics macro's identical
per-run filenames from colliding. Retain all ROOT rollover files when later
combining the segments. Job stdout/stderr are under `/farm_out/cploen/WORKFLOW`,
with separate files for each attempt.

The provenance directory contains the committed replay snapshot (including
coin kinematics), its commit ID and kinematics checksum, the verified matrix
checksums, run/setting/segment mapping, raw-file sizes, run list and exact SWIF
commands. The worker stages `jobs/setup_elastic_farm.sh`, which loads
`nps_replay/5.28.24`, matching the saved angular-sandbox `run_one_optics.sh`
from commit `f76e9065922ac5fe59df4311c3d4a30a9f2bca9e`. It then sources the
snapshot's `setup.sh`. The setup script is copied into the workflow's
provenance and its checksum is recorded. `--setup` can select another script.
The missing `/u/group/nps/cploen/hcswif/setup.sh` is not required.

Default resources match the uploaded `swif2_stuff` jobs: `hallc`, `production`,
`el9`, one core, 3 GB RAM and 24 hours. Scratch space is at least 50 GB or four
times the raw segment size, plus the staged inputs. `--ram`, `--time`,
`--account`, `--partition` and `--constraint` can be
set to the values appropriate to your established farm configuration.

Omit `--submit` to print the complete run/segment plan without creating a
workflow. `--submit` prepares all jobs and then starts the entire workflow;
there is no preliminary subset. If adding a job fails, the new workflow
remains paused and the error is reported. Inspect that workflow before retrying.

SWIF2 input/output staging and resource syntax follow the
[JLab add-job documentation](https://scicomp.jlab.org/cli/add-job.html).
Farm execution and real elastic-event reconstruction must be checked on ifarm.
