# Sieve and elastic replay with the angular and delta calibration

The November 5 calibration combines the constrained YTAR-zero angular refit
with sparse elastic delta corrections. The existing nonconstant angular and
x-target-dependent coefficients are retained. Nonconstant delta corrections
are added by exponent code. All constants are applied exactly once through
momentum-specific flags, with `00000` only a matrix-header comment.
`hphi_offset` is XPTAR in radians, `htheta_offset` is YPTAR in radians, and
`hdelta_offset` is fractional delta. The historical percent comment for the
last flag was incorrect for deployed hcana 1.1. See
[the calibration record](../README_HMS_ANGULAR_DELTA.md).

The two established run lists contain 41 sieve runs and 11 elastic runs.
Run 1253 retains htheta_lab = -22.120 degrees. Preparation uses a clean
committed checkout, with one job per complete run and all available contiguous
raw segments staged from `/mss/hallc/c-nps/raw`. Missing segment 0, gaps, or
nonpositive MSS file sizes stop preparation. Every run replays all events (-1).

On ifarm, prepare both samples without submitting:

```bash
python3 jobs/prepare_angular_delta_replays.py
```

For a read-only coverage plan, add `--plan`. The campaign configuration and
exact expected run identities are in
`config/hms_angular_delta_20261105/replay_campaign.json`. To prepare a separate
attempt use `--workflow-suffix v2` and, if needed, `--output-root PATH`.
The single-sample interface remains available:

```bash
python3 jobs/submit_elastic_swif.py jobs/elastic_oct29_runs.txt \
  --sample elastic --workflow hms_elastic_angdelta_ytar0_fullrun_20261105 --prepare
python3 jobs/submit_elastic_swif.py jobs/sieve_oct29_runs.txt \
  --sample sieve --workflow hms_sieve_angdelta_ytar0_fullrun_20261105 --prepare
```

`elastic_oct29_runs.txt` contains the 11 runs confirmed by Christine on
November 3, 2026: 1714–1716 at 5.878 GeV/c; 1250, 1251, 1252, 1253 and 1259
at 6.117 GeV/c; and 1534–1536 at 6.667 GeV/c. Another one-run-per-line list
can be supplied as the positional argument.

The worker uses the existing `SCRIPTS/NPS/OPTICS/replay_optics_coin_NPS_HMS.C`
without changing its physics or output definitions. Each job gets a separate
scratch directory. It reads all its staged raw segments from `.` and writes to
`ROOTfiles/OPTICS` and `REPORT_OUTPUT/HMS`. ROOT files are checked there with
the existing `check_root` program before SWIF copies outputs to volatile.

The two samples share the dated parent:

```text
/volatile/hallc/nps/cploen/ROOTfiles/
  nov05_angular_delta_matrix_flags_offsets_ytar0_refit_20261105/
    OPTICS/SIEVE/WORKFLOW/SETTING/run_RUN/{rootfiles,reports}/
    ELASTIC/WORKFLOW/SETTING/run_RUN/{rootfiles,reports}/
```

Each sample workflow also contains `provenance/manifest.json`, a frozen Git
archive `nps_replay.tar.gz`, setup and worker copies, the run list, exact SWIF
commands, and `submit_prepared.sh`. `provenance/runtime_config` contains the
actual committed matrices, HMS flags, momentum-specific optics parameters,
calibration manifest and run databases extracted from the job tarball.
Hashes are checked against the requested calibration during preparation and
again by each worker before replay. The full archive retains the other
calibration files. It is independent of later edits to the live checkout.

After preparation, run each printed `provenance/submit_prepared.sh` on ifarm
once to create and start that sample's workflow. The saved script submits its
already frozen snapshot. `--submit` instead prepares and immediately starts a
new workflow. No jobs are queued by the default two-sample preparation command.
Output directories must not already exist; earlier workflows are preserved.

The snapshot retains the corrected 1253 kinematics, source commit, matrix and
flag hashes, all zero-order constants with units, source-fit provenance,
run/setting/segment mapping, raw-file sizes and checksums of the setup and run
databases. The worker uses `jobs/setup_elastic_farm.sh`, loads
`nps_replay/5.28.24`, and sources the snapshot's setup.sh as in the preceding
campaign. A different setup may be selected with `--setup`.

Default resources match the uploaded `swif2_stuff` jobs: `hallc`, `production`,
`el9`, one core, 3 GB RAM and 24 hours per complete run. Scratch space is at least 50 GB or four
times the total raw-file size for that run, plus the staged inputs. `--ram`, `--time`,
`--account`, `--partition` and `--constraint` can be
set to the values appropriate to your established farm configuration.

With neither `--prepare` nor `--submit`, the single-sample launcher prints
a plan only. If adding a job fails during submission, the workflow remains
paused and the error is reported. Inspect it before retrying the saved script.
Do not rerun a script that already created a workflow without first assessing
its state. Job stdout/stderr remain under `/farm_out/cploen/WORKFLOW`.

SWIF2 input/output staging and resource syntax follow the
[JLab add-job documentation](https://scicomp.jlab.org/cli/add-job.html).
Farm execution and real elastic-event reconstruction must be checked on ifarm.

## Sieve replay

The list contains 41 runs: 11 at 5.878, 14 at 6.117 and 16 at 6.667 GeV/c.
It uses the physical-run lists uploaded in `cploen/ifarm-swif2-handoff`
commit `88501c6c7b664a1524719494f5bd8fccfa0f4be1`, adds 7008 as documented
in the October 29 campaign runbook, and excludes 1242, marked junk there.
Previously deferred 1961 and 5165–5167 are included for this full replay test.

Sieve and elastic data use separate folders beneath the shared November 5
parent. They use the same calibration, all-event optics macro, full-run staging,
and frozen-configuration rules. Existing campaigns will not acquire the new
constants when resumed; submit a newly prepared snapshot for this calibration.
