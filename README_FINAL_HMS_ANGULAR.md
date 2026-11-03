# Final HMS angular matrices for elastic replay

Branch: `codex/final-hms-angular-20261029`, based on the fork's `develop`
commit `82f6fa3bc8aae79298b649a8e83523c6ee39797a`.

The three matrices were generated on October 29, 2026 (ifarm file dates
confirmed by Christine) and exported from
`cploen/hallc_spectrometer_angular_optics` commit
`4b1db54e7b718261941413cb0086dd807f54f772`.

| Setting (GeV/c) | Campaign source | Installed matrix |
| --- | --- | --- |
| 5.878 | `HMS_5p878GeV/06e_beam_search/beam20_inner10/matrices/beam.dat` | `DATFILES/nps_hms_optics_5p878_ang.dat` |
| 6.117 | `HMS_6p117GeV/06e_beam_search/beam20_inner20/matrices/beam.dat` | `DATFILES/nps_hms_optics_6p117_ang.dat` |
| 6.667 | `HMS_6p667GeV_joint_min5/06e_beam_search/beam20_inner20/matrices/beam.dat` | `DATFILES/nps_hms_optics_6p667_ang.dat` |

The installed files are byte-for-byte copies of the exported matrices:

```text
c04a1138c2f71a06afb81a7ca6dfc57267940f06e5557220efd9b055b7cff7d7  DATFILES/nps_hms_optics_5p878_ang.dat
149615a502a8bc1040b179cda4c984f7a113a04c86a5a8fe1f24da2fb543a354  DATFILES/nps_hms_optics_6p117_ang.dat
43b5b88bdc70f5c0a7f5f11aec3a5462af52051d52c149a3889fe8ec47dd9c58  DATFILES/nps_hms_optics_6p667_ang.dat
```

All fitted `00000` terms are included in the matrix, including YTAR.
In each corresponding `PARAM/HMS/GEN/hmsflags_<setting>.param`,
`htheta_offset` (YPTAR) and `hphi_offset` (XPTAR) are zero.
Do not add the historical angular offsets or the fitted constants again.

The delta column and every XTAR-dependent coefficient agree with the
existing `develop` matrices. Momentum and central-angle offsets are unchanged.
The existing `DBASE/NPS/standard_coin.database` run ranges select the
setting-specific `hcana_<setting>.param`, which loads the matching flags
and matrix. Database, kinematics, replay macros and other settings are unchanged.

Validation covers file checksums, matrix syntax and finite coefficients,
the frozen coefficients, the offset assignments and the configuration paths.
Full hcana replay on real elastic events remains to be run on ifarm.
