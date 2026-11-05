# HMS angular and delta calibration November 5 2026

This branch combines the November 3 angular refit with the November 4 elastic
delta corrections, packaged on November 5. It retains run 1253 at
`htheta_lab = -22.120` degrees in `DBASE/NPS/standard_coin.kinematics`.

The three momentum-specific matrices retain their angular columns, higher-order
baseline delta terms, and x-target-dependent terms. Sparse nonconstant delta
corrections are added to the corresponding coefficients by exponent code.
The matrix headers record all fitted zero-order values as comments. No active
`00000` record is used: constants are applied once through the matching flags.
YTAR's **zero-order coefficient** was held fixed at zero; there is no external
YTAR offset in replay. Its nonconstant reconstruction coefficients remain in
the angular matrix.

| Setting GeV/c | hphi_offset XPTAR rad | htheta_offset YPTAR rad | hdelta_offset fractional delta |
|---|---:|---:|---:|
| 5.878 | 0.0015452061252705057 | 0.00044623110164892805 | -0.00043460784625504845 |
| 6.117 | 0.0016898981513098635 | 0.0005329998924736663 | -0.00023708000243836876 |
| 6.667 | 0.0020566023391089734 | 0.00053123777935165 | 0.00027015716004233256 |

`hdelta_offset` is **fractional delta**, despite the old flags annotation of
percent. The deployed hcana 1.1 source adds it to the matrix delta sum and
subsequently multiplies by 100 for `H.gtr.dp`. The resulting constant shifts in
that percent-valued branch are -0.0434607846, -0.0237080002, and +0.0270157160
percentage points, respectively. Moving the fit's constant from its active
matrix record into this flag preserves the fitted reconstructed momentum.

`config/hms_angular_delta_20261105/fit_manifest.json` records the exact
correction coefficients, source hashes, matrix/flag hashes, conventions,
SIMC targets, fit results, dates, and the deployed offset-unit source check.
The 6.117 coefficient transfer was checked against its canonical payload
SHA256 and the reconstructed original export hash. The fits are candidates
for replay testing; their 14/15/23 terms describe sparse **corrections** to
the existing delta polynomial, not replacement complete matrices.

## Prepare the replay campaign on ifarm

After checking out this branch in a clean checkout:

```bash
python3 jobs/prepare_angular_delta_replays.py
```

This prepares all 41 established sieve runs and 11 elastic runs, all events,
with one job per complete run and every contiguous raw segment staged from
MSS. It writes frozen replay tarballs, explicit runtime configuration copies,
checksums, manifests, exact SWIF commands, and a `submit_prepared.sh` script
for each sample. It does not queue jobs. `--plan` only checks and prints the
run/segment plan. `--workflow-suffix v2` prepares a separate attempt without
overwriting an existing workflow directory.

The shared volatile parent is:

```text
/volatile/hallc/nps/cploen/ROOTfiles/
  nov05_angular_delta_matrix_flags_offsets_ytar0_refit_20261105/
    OPTICS/SIEVE/hms_sieve_angdelta_ytar0_fullrun_20261105/
    ELASTIC/hms_elastic_angdelta_ytar0_fullrun_20261105/
```

The parent and sample names are specified in
`config/hms_angular_delta_20261105/replay_campaign.json`.
Every sample contains `<setting>/run_<run>/rootfiles`, `reports`, and
`provenance/runtime_config`. The latter contains copies of the exact committed
matrices, flags, optics parameters and run databases extracted from the job
tarball, with their repository-relative paths intact. Workers verify the
runtime files against the manifest before replay. The complete Git archive
preserves the remaining detector and analysis configuration.

To queue a prepared campaign, run its saved script on ifarm:

```bash
bash /path/printed/by/preparation/provenance/submit_prepared.sh
```

Run each saved script once. It creates and starts that sample's workflow using
the already frozen snapshot; it does not read a subsequently edited checkout.
Alternatively, `python3 jobs/prepare_angular_delta_replays.py --submit` prepares
and immediately submits both samples in new output directories. See
`jobs/README_ELASTIC_SWIF.md` for resources, naming, raw-file handling, and run
list provenance. Existing campaigns are preserved and do not acquire changes
from this branch.
