# OpenCoulomb v0.2.0 — Full Feature Test Report

Generated: 2026-02-27 18:25:38


---

OpenCoulomb v0.2.0 — Full Feature Demo

---

Version: 0.2.0


## 1. Basic CFS Computation (strike-slip)

Model: This is a test file for the Coulomb 1.0
Sources: 2, Grid: 61x61
Compute time: 0.042s
Peak CFS: 5.0305 bar
Min  CFS: -4.9307 bar


## 2. CFS Map

![01_cfs_map_strikeslip.png](01_cfs_map_strikeslip.png)


## 3. Displacement Field

![02_displacement_strikeslip.png](02_displacement_strikeslip.png)


## 4. Cross-Section

Section shape: (31, 25)
![03_cross_section_strikeslip.png](03_cross_section_strikeslip.png)



## 5. Oblique Thrust Fault Model

Model: This is a test file for the Coulomb 1.0
Peak CFS: 0.1903 bar
![04_cfs_map_thrust.png](04_cfs_map_thrust.png)

![05_cross_section_thrust.png](05_cross_section_thrust.png)



## 6. Output Writers

  -> wrote strikeslip.csv, .cou, .dat, _summary.txt


## 7. Scaling Relations

 Mag | WC94 L(km) | WC94 W(km) |  WC94 D(m) |   Blaser L |   Blaser W
----------------------------------------------------------------------
 5.0 |       1.70 |       3.89 |      0.045 |       3.24 |       3.89
 5.5 |       3.76 |       5.62 |      0.099 |       6.76 |       5.62
 6.0 |       8.32 |       8.13 |      0.219 |      14.13 |       8.13
 6.5 |      18.41 |      11.75 |      0.484 |      29.51 |      11.75
 7.0 |      40.74 |      16.98 |      1.072 |      61.66 |      16.98
 7.5 |      90.16 |      24.55 |      2.371 |     128.82 |      24.55
 8.0 |     199.53 |      35.48 |      5.248 |     269.15 |      35.48
![06_scaling_relations.png](06_scaling_relations.png)

M7.0 fault: length=0.0 km, depth=0.0-17.0 km


## 8. Strain Computation

Strain computed: True
Volumetric strain range: [-6.83e-06, 6.71e-06]
![07_strain_tensor.png](07_strain_tensor.png)

![08_volumetric_strain.png](08_volumetric_strain.png)



## 9. Slip Tapering

![09_taper_profiles.png](09_taper_profiles.png)

Tapered peak CFS: 3.0440 bar (vs 5.0305 untapered)
![10_taper_comparison.png](10_taper_comparison.png)



## 10. 3D Volume Computation

Volume: 61x61x10 = 37210 points
Depths: [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0] km
Volume compute time: 0.1s
3D CFS shape: (10, 61, 61)
3D CFS range: [-6.6438, 5094.7227] bar


## 11. Volume Depth Slices

![11_volume_slices.png](11_volume_slices.png)


## 12. Volume Cross-Sections

![12_volume_cross_sections.png](12_volume_cross_sections.png)


## 13. 3D Volume Scatter Plot

  -> SKIPPED (matplotlib 3D projection unavailable: ValueError("Unknown projection '3d'"))

## 14. Animated Volume GIF

  -> saved 14_volume_depth_animation.gif (87 KB)


## 15. Volume Output Files

  -> wrote volume_3d.csv (7350 KB)
  -> wrote 10 depth slice .dat files to volume_slices/


## 16. Synthetic Earthquake Catalog

Created 50 synthetic events
CSV round-trip: 50 events recovered
Filtered: 21 events M>=4.0, 19 events depth<=10km


## 17. Catalog Overlay on Volume Slice

![15_catalog_on_volume.png](15_catalog_on_volume.png)


## 18. Beachball Focal Mechanisms

![16_beachballs.png](16_beachballs.png)


## 19. Beachballs on CFS Map

![17_beachballs_on_map.png](17_beachballs_on_map.png)

![18_beachballs_with_catalog.png](18_beachballs_with_catalog.png)



## 20. GPS Displacement Comparison

Created 12 synthetic GPS stations
![19_gps_horizontal.png](19_gps_horizontal.png)

![20_gps_vertical.png](20_gps_vertical.png)

GPS Misfit:
  RMS horizontal: 0.003938 m
  RMS vertical:   0.001802 m
  RMS 3D:         0.004331 m
  Reduction of variance: 0.9841
  -> saved synthetic_gps.csv


## 21. Subfaulted Source (101 patches)

Sources: 101
Compute time: 0.399s
Peak CFS: 5.0305 bar
![21_subfaulted_cfs.png](21_subfaulted_cfs.png)



## 22. Volume Fields: CFS, Shear, Normal

![22_volume_fields.png](22_volume_fields.png)



## 23. Volume + Tapering

Tapered volume peak CFS: 209.7315 bar
![23_volume_tapered_slices.png](23_volume_tapered_slices.png)




---

SUMMARY

---

Total images generated: 22
  01_cfs_map_strikeslip.png (91 KB)
  02_displacement_strikeslip.png (248 KB)
  03_cross_section_strikeslip.png (76 KB)
  04_cfs_map_thrust.png (117 KB)
  05_cross_section_thrust.png (95 KB)
  06_scaling_relations.png (144 KB)
  07_strain_tensor.png (166 KB)
  08_volumetric_strain.png (51 KB)
  09_taper_profiles.png (226 KB)
  10_taper_comparison.png (80 KB)
  11_volume_slices.png (154 KB)
  12_volume_cross_sections.png (108 KB)
  15_catalog_on_volume.png (71 KB)
  16_beachballs.png (74 KB)
  17_beachballs_on_map.png (85 KB)
  18_beachballs_with_catalog.png (113 KB)
  19_gps_horizontal.png (75 KB)
  20_gps_vertical.png (64 KB)
  21_subfaulted_cfs.png (87 KB)
  22_volume_fields.png (97 KB)
  23_volume_tapered_slices.png (50 KB)
  14_volume_depth_animation.gif (87 KB)

Total data files: 7
  strikeslip.csv (672 KB)
  synthetic_catalog.csv (5 KB)
  synthetic_gps.csv (2 KB)
  volume_3d.csv (7350 KB)
  strikeslip_dcff.cou (487 KB)
  strikeslip_cfs.dat (47 KB)
  strikeslip_summary.txt (1 KB)
