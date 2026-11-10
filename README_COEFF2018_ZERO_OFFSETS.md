# Updated 2018 matrix replay test

This branch replays the NPS optics sieve/slit physical-run lists with the
**updated Beam matrix fitted from the 2018 campaign**, not the original 2018
starting matrix. All four momentum settings select one common coefficient file:
`DATFILES/hms_recon_coeff2018_new_zero_offsets.dat`.

The complete active `00000` row is removed after the fit. All other transport
rows and their four coefficient columns are preserved exactly, including the
source delta and XTAR-dependent terms. No removed constant is transferred to
flags. All external HMS reconstruction offsets, momentum factor and central
offsets in the selected flags files are zero. This is the requested replay test;
it is not a new constrained coefficient fit. The source fit had a free YTAR
intercept. Future coefficient fits must explicitly fix `ytar_00000 = 0`.

## Prepare the calibration

From a new isolated worktree based on the frozen Nov05 replay, run:

```bash
A=/u/group/nps/cploen/ML_HMS_OPTICS_JOINT_SURFACE
B="$A/HMS_LowMom_LowDelta_2018_Accepted/06e_beam_search/beam30_inner20"
python3 jobs/prepare_coeff2018_zero_offsets.py \
  --matrix "$B/matrices/beam.dat" --beam-manifest "$B/manifest.json"
```

The builder verifies the source against its completed Beam manifest, removes
only the constant row, updates the three existing high-momentum optics/flag
files, and adds an explicit 4.637 GeV optics configuration for runs 2184–2187.
The general 4.637 GeV optics parameters and flags are inherited from the optics
configuration previously selected by those runs. Detector calibrations,
kinematics and the known run-1253 angle correction are preserved.

The frozen calibration, source hashes, removed row, run list and every resolved
run-to-matrix assignment are written under
`config/coeff2018_new_zero_offsets_20261110/`. The four groups contain 4, 11,
14 and 16 runs at 4.637, 5.878, 6.117 and 6.667 GeV/c respectively: 45 distinct
complete physical runs. Run 1242 remains excluded as previously documented.
Previously deferred 1961 and 5165–5167 are retained in this full replay test.

## Plan, freeze, and submit

The existing submission interface now accepts an explicit calibration manifest;
its Nov05 default is unchanged. First obtain a read-only plan:

```bash
CFG=config/coeff2018_new_zero_offsets_20261110
OUT=/volatile/hallc/nps/cploen/ROOTfiles/coeff2018_new_zero_offsets
WF=hms_sieve_coeff2018_new_zero_offsets_20261110
python3 jobs/submit_elastic_swif.py "$CFG/sieve_runs.txt" \
  --sample sieve --calibration "$CFG/fit_manifest.json" \
  --output "$OUT/OPTICS/SIEVE" --workflow "$WF"
```

After the branch changes are validated and committed, run the same command
with `--prepare`. This creates a frozen Git archive and runtime/config checksums
without queuing work. Submit that exact snapshot once with the printed
`provenance/submit_prepared.sh` command. The alternative `--submit` prepares
and starts a new workflow immediately. Do not resubmit an existing workflow.

Each job processes all events and all contiguous raw segments, including segment
0, using the unchanged optics replay macro and established farm environment.
Each worker verifies the frozen runtime hashes and independently resolves its
run through the frozen database, optics parameters and flags. It prints the
effective updated matrix path and checksum before replay. A wrong assignment,
unexpected checksum, nonzero external offset or active constant row stops the
job. These checks are repeated against the files extracted from the actual
job snapshot, not the mutable live checkout.

Products are under
`$OUT/OPTICS/SIEVE/$WF/SETTING/run_RUN/{rootfiles,reports}/`.
The workflow's `provenance/` holds the snapshot, 45-run list, effective
assignments, setup/worker copies and exact submission commands. Monitor with:

```bash
swif2 status "$WF" -jobs
```

No elastic runs are added by this sieve/slit submission. Refitting campaigns
will use the new replay products and this exact zero-offset matrix as their
starting `oldfit.dat`, with extended delta slices and the previously accepted
watershed/tail-pruning and sheet-fit policies.
