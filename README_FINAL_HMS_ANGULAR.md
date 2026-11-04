# HMS angular matrices with constrained YTAR

Branch: `codex/final-hms-angular-20261029` in `cploen/nps_replay`.

These matrices replace the original October 29 beam-search exports with
the constrained YTAR refits in `07_diagnostics/ytar_zero_refit_20261103/`.
They use the saved beam-selected basis, fix the YTAR `00000` coefficient
to exactly zero, and refit the remaining adjustable YTAR coefficients.
XPTAR, YPTAR, momentum and all XTAR-dependent coefficients are unchanged.

Source: `cploen/hallc_spectrometer_angular_optics` commit
`d7c8311763adb843698ca8028f24064f9527f64a`, exported on November 4, 2026.

| Setting (GeV/c) | Campaign source | Installed matrix |
| --- | --- | --- |
| 5.878 | `HMS_5p878GeV/07_diagnostics/ytar_zero_refit_20261103/ytar_zero.dat` | `DATFILES/nps_hms_optics_5p878_ang.dat` |
| 6.117 | `HMS_6p117GeV/07_diagnostics/ytar_zero_refit_20261103/ytar_zero.dat` | `DATFILES/nps_hms_optics_6p117_ang.dat` |
| 6.667 | `HMS_6p667GeV_joint_min5/07_diagnostics/ytar_zero_refit_20261103/ytar_zero.dat` | `DATFILES/nps_hms_optics_6p667_ang.dat` |

The constrained exports are converted to the established replay format:
the `00000` row is recorded only as a comment before the matrix-data
delimiter, and its angular constants are placed in the matching flags file.
Every nonconstant coefficient is retained exactly. Installed checksums:

```text
7dfd7bed25303550a1d357dbab74aca1e6a48a2d070b4fd65488fa1743e4cc13  DATFILES/nps_hms_optics_5p878_ang.dat
0e876c4febc14d8a89800811b54562d5f7ae6c0be2eeebbd399c66e051674125  DATFILES/nps_hms_optics_6p117_ang.dat
07f4f7b6cf6cbac8b0b163ebb24b43f2578a21aaf116bec020a7c4baab5c6b19  DATFILES/nps_hms_optics_6p667_ang.dat
```

Each campaign uses one shared matrix across all its rungroups: eight for
5.878, five for 6.117 and seven for 6.667 GeV/c. The special May reference
for two 6.667 rungroups was used only to reproduce their original replay
in closure diagnostics; it is not installed for any full-replay subgroup.

YTAR's constant is zero by constraint. Angular constants are applied exactly
once through `PARAM/HMS/GEN/hmsflags_<setting>.param`. No active `00000`
row is present in the matrix-data block. The commented reference row
appears before the first delimiter, matching the pre-existing replay files.

| Setting (GeV/c) | `hphi_offset` (XPTAR, rad) | `htheta_offset` (YPTAR, rad) |
| --- | ---: | ---: |
| 5.878 | 1.5452061252705057e-03 | 4.4623110164892805e-04 |
| 6.117 | 1.6898981513098635e-03 | 5.3299989247366630e-04 |
| 6.667 | 2.0566023391089734e-03 | 5.3123777935165000e-04 |

The existing `DBASE/NPS/standard_coin.database` run ranges select the
setting-specific `hcana_<setting>.param`, which loads the matching flags
and matrix. Coin kinematics and the confirmed 11-run elastic list are retained.

Validation checked source Git blob IDs and installed SHA-256 checksums,
unchanged nonconstant polynomial rows, exactly zero source YTAR constants,
the saved YTAR basis, matching angular flags, no active constant row, and
configuration selection for all 11 elastic runs. Polynomial predictions
from the converted matrix plus flags are checked against the constrained
source matrices. This is not a full event replay validation.

The batch launcher pins the new checksums and writes a distinct output folder:
`oct29_beam_search_matrix_flags_offsets_ytar0_refit_20261103`.
See `jobs/README_ELASTIC_SWIF.md` for submission.

The already submitted `hms_elastic_ytar0_20261104` workflow contains the
previous snapshot. Pulling this correction cannot change that snapshot.
Keep it paused and submit a new workflow with the corrected configuration.
