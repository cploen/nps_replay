# Elastic replay with the constrained YTAR refit

The installed matrices use the saved October 29 beam-selected basis, with
YTAR's constant fixed at zero and the other adjustable YTAR coefficients
refitted. Nonconstant XPTAR, YPTAR and momentum coefficients are unchanged.
The fitted XPTAR and YPTAR constants are applied through `hphi_offset` and
`htheta_offset` in the momentum-specific `hmsflags` files. The `00000` row
is a comment in the matrix header, outside the active coefficient block.

Use `submit_elastic_swif.py` on ifarm with an explicit text file containing
one elastic run number per line. Blank lines and `#` comments are allowed.
Every available numeric segment under `/mss/hallc/c-nps/raw` is queued in
one SWIF2 workflow. All events are replayed (`-1`), with one job per segment.

```bash
python3 jobs/submit_elastic_swif.py jobs/elastic_oct29_runs.txt --submit
```

`elastic_oct29_runs.txt` contains the 11 runs confirmed by Christine on
November 3, 2026: 1714–1716 at 5.878 GeV/c; 1250, 1251, 1252, 1253 and 1259
at 6.117 GeV/c; and 1534–1536 at 6.667 GeV/c. Another one-run-per-line list
can be supplied as the positional argument.

The worker uses the existing `SCRIPTS/NPS/OPTICS/replay_optics_coin_NPS_HMS.C`
without changing its physics or output definitions. Each job gets a separate
scratch directory. It reads its staged raw segment from `.` and writes to
`ROOTfiles/OPTICS` and `REPORT_OUTPUT/HMS`. ROOT files are checked there with
the existing `check_root` program before SWIF copies outputs to volatile.

The output hierarchy is:

```text
/volatile/hallc/nps/cploen/ROOTfiles/ELASTIC/
  oct29_beam_search_matrix_flags_offsets_ytar0_refit_20261103/WORKFLOW/
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
checksums, source-matrix checksums, fitted angular offsets in radians,
run/setting/segment mapping, raw-file sizes, run list and exact SWIF
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

## Sieve replay

The same launcher and optics macro also support the sieve test:

```bash
python3 jobs/submit_elastic_swif.py jobs/sieve_oct29_runs.txt \
  --sample sieve --workflow hms_sieve_ytar0_flags_20261104 --submit
```

The list contains 41 runs: 11 at 5.878, 14 at 6.117 and 16 at 6.667 GeV/c.
It uses the physical-run lists uploaded in `cploen/ifarm-swif2-handoff`
commit `88501c6c7b664a1524719494f5bd8fccfa0f4be1`, adds 7008 as documented
in the October 29 campaign runbook, and excludes 1242, marked junk there.
Previously deferred 1961 and 5165–5167 are included for this full replay test.

`--sample sieve` selects a separate default output directory:
`/volatile/hallc/nps/cploen/ROOTfiles/OPTICS/SIEVE/oct29_beam_search_matrix_flags_offsets_ytar0_refit_20261103/WORKFLOW/`.
Job names and saved run-list provenance are labeled `sieve`. The matrices,
flags, all-event replay, per-segment staging and farm resources are the same
as the corrected elastic workflow. The elastic workflow can continue running.

After pulling a configuration correction, submit a new workflow. Existing
workflows retain their archived snapshot and will not acquire the correction
when resumed. For this flags-convention correction, use a fresh name such
as `hms_elastic_ytar0_flags_20261104`.
