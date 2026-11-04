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

The installed files are byte-for-byte copies of the constrained exports:

```text
855aecc8205a17b8e42d9867f61b2da7c7eb6655b1af8628cb56e3cf82468772  DATFILES/nps_hms_optics_5p878_ang.dat
067a0187901d08a00f62171f0d34a9e5932f85c077eabfee55da88a1fda41355  DATFILES/nps_hms_optics_6p117_ang.dat
d60928e0b0ac81347431e30fd5bb6355faed121b2f16d70ee9c90e8fd599b76d  DATFILES/nps_hms_optics_6p667_ang.dat
```

Each campaign uses one shared matrix across all its rungroups: eight for
5.878, five for 6.117 and seven for 6.667 GeV/c. The special May reference
for two 6.667 rungroups was used only to reproduce their original replay
in closure diagnostics; it is not installed for any full-replay subgroup.

The fitted angular `00000` terms remain in the matrix. YTAR's constant is
zero by constraint. In each matching `PARAM/HMS/GEN/hmsflags_<setting>.param`,
`htheta_offset` (YPTAR) and `hphi_offset` (XPTAR) remain zero. Do not add
historical angular offsets or the fitted constants a second time.

The existing `DBASE/NPS/standard_coin.database` run ranges select the
setting-specific `hcana_<setting>.param`, which loads the matching flags
and matrix. Coin kinematics and the confirmed 11-run elastic list are retained.

Validation checked source Git blob IDs and installed SHA-256 checksums,
identical polynomial rows, exactly zero YTAR constants, the saved YTAR
basis, unchanged other matrix columns and XTAR-dependent terms, and
configuration selection for all 11 elastic runs. The constrained matrices
have been evaluated in diagnostics; full replay on ifarm is still pending.

The batch launcher pins the new checksums and writes a distinct output folder:
`oct29_beam_search_matrix_embedded_offsets_ytar0_refit_20261103`.
See `jobs/README_ELASTIC_SWIF.md` for submission.
