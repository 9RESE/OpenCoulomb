# File Format Reference

Complete specification of all file formats read and written by OpenCoulomb.

---

## Input: .inp (Coulomb input file)

The `.inp` format is the native input format of Coulomb 3.4 (USGS). OpenCoulomb
reads `.inp` files directly.

### Overall structure

```
Line 1:  Free text title
Line 2:  Free text comment
         Material parameters block
         Regional stress block
         Fault table(s)
         Grid Parameters block
         [Size Parameters block]  (optional)
         [Cross section default block]  (optional)
```

### Material parameters block

```
#reg1=  0  #reg2=  0  #fixed=  1  sym=  1
 PR1=       0.250 PR2=       0.250 DEPTH=      10.000
  E1=  0.800000E+06  E2=  0.800000E+06 XLIM=     0.000 YLIM=     0.000
FRIC=       0.400
```

| Field | Description | Unit |
|-------|-------------|------|
| `PR1`, `PR2` | Poisson's ratio (region 1, 2) | dimensionless |
| `DEPTH` | Default computation depth | km |
| `E1`, `E2` | Young's modulus | bar |
| `XLIM`, `YLIM` | Symmetry axes (0 = none) | km |
| `FRIC` | Coefficient of friction | dimensionless |

Accepted aliases: `XSYM`=`XLIM`, `YSYM`=`YLIM`.

### Regional stress block

```
  S1DR=  189.0000 S1DP=   -0.0001 S1IN=  100.000  S1GD=   0.000
  S3DR=   99.0000 S3DP=    0.0000 S3IN=    0.000  S3GD=   0.000
  S2DR=  270.0001 S2DP=  -89.999  S2IN=    0.000  S2GD=   0.000
```

For each principal stress axis (S1, S2, S3):

| Suffix | Description | Unit |
|--------|-------------|------|
| `DR` | Azimuth (degrees from North, clockwise) | degrees |
| `DP` | Plunge (negative = downward) | degrees |
| `IN` | Magnitude | bar |
| `GD` | Vertical gradient | bar/km |

### Fault table block

Each fault table is preceded by a two-line header:

```
  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot
 xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx
    1    -20.000     0.000     20.000     0.000  100      1.000     0.000    90.000     0.000    15.000  Main fault
```

Fault line columns:

| Column | Description | Unit |
|--------|-------------|------|
| Index | Row number (informational) | — |
| X-start | Surface trace start (east positive) | km |
| Y-start | Surface trace start (north positive) | km |
| X-fin | Surface trace end | km |
| Y-fin | Surface trace end | km |
| Kode | Fault type (100=dislocation, 200=tensile, 300=intrusion, 400=ellipsoid, 500=point) | integer |
| rt.lat | Right-lateral slip (positive = right-lateral) | m |
| reverse | Reverse slip (positive = reverse/thrust) | m |
| dip | Dip angle from horizontal | degrees |
| top | Top depth (positive downward) | km |
| bot | Bottom depth (positive downward) | km |
| Label | Optional free text label | — |

**Source vs receiver**: faults with `rt.lat=0` and `reverse=0` are receivers.

Multiple table blocks are allowed. Each block begins with its own two-line header.

### Grid Parameters block

```
Grid Parameters
  1  ---  Start-x =    -100.000
  2  ---  Start-y =    -100.000
  3  ---  Finish-x =    100.000
  4  ---  Finish-y =    100.000
  5  ---  x-increment =   2.000
  6  ---  y-increment =   2.000
```

The parser accepts varied spacing around `=` and dashes of any length.

### Size Parameters block (optional)

```
   Size Parameters
  1  --------------------------  Plot size =        1.0000000
  2  --------------  Shade/Color increment =        0.2000000
  3  ------  Exaggeration for disp.& dist. =    10000.0000000
```

Read but not used for computation. Present in Coulomb 3.4 example files.

### Cross section default block (optional)

```
   Cross section default
  1  ---  Start-x =       0.000
  2  ---  Start-y =       0.000
  3  ---  Finish-x =      50.000
  4  ---  Finish-y =      50.000
  5  ---  Distant-increment =   1.000
  6  ---  Z-depth =      -30.000
  7  ---  Z-increment =    1.000
```

| Field | Description | Unit |
|-------|-------------|------|
| Start-x, Start-y | Cross-section start point | km |
| Finish-x, Finish-y | Cross-section end point | km |
| Distant-increment | Along-profile spacing | km |
| Z-depth | Maximum depth (negative = below surface) | km |
| Z-increment | Depth spacing | km |

---

## Output: .cou (Coulomb binary/text format)

Written by `opencoulomb compute` as `{stem}_dcff.cou`.

Compatible with Coulomb 3.4. Contains the CFS grid and metadata in the
structured text format Coulomb uses internally. This file can be read back into
Coulomb 3.4 for further plotting.

---

## Output: .csv

Written by `opencoulomb compute` as `{stem}.csv`.

### Header

```
x_km,y_km,cfs_bar,shear_bar,normal_bar,ux_m,uy_m,uz_m
```

### Columns

| Column | Description | Unit |
|--------|-------------|------|
| `x_km` | East position | km |
| `y_km` | North position | km |
| `cfs_bar` | Coulomb failure stress | bar |
| `shear_bar` | Shear stress change | bar |
| `normal_bar` | Normal stress change | bar |
| `ux_m` | East displacement | m |
| `uy_m` | North displacement | m |
| `uz_m` | Vertical displacement (positive up) | m |

One row per grid point. Points are ordered row by row (y varies slowest).

### Reading in Python

```python
import numpy as np

data = np.genfromtxt("model.csv", delimiter=",", names=True)
print(data["cfs_bar"].max())
```

Or with pandas:

```python
import pandas as pd

df = pd.read_csv("model.csv")
print(df.describe())
```

---

## Output: .dat (plain text grid)

Written by `opencoulomb compute` as `{stem}_{field}.dat`.

Plain whitespace-delimited text, one value per line corresponding to grid
points ordered (x varies fastest):

```
x1_km  y1_km  value1
x2_km  y1_km  value2
...
```

Compatible with GMT (`grd2xyz` column format) and easy to import:

```python
import numpy as np

data = np.loadtxt("model_cfs.dat")
x, y, cfs = data[:, 0], data[:, 1], data[:, 2]
```

The `--field` option selects which stress component is written:

| Value | Column written |
|-------|---------------|
| `cfs` (default) | Coulomb failure stress |
| `shear` | Shear stress |
| `normal` | Normal stress |

---

## Output: _summary.txt

Written by `opencoulomb compute` as `{stem}_summary.txt`.

Human-readable text file reporting:

- Model title and file path
- Material parameters
- Fault list (geometry and slip)
- Grid specification
- Peak CFS, shear, and normal stress values
- Computation timestamp

---

## Output: _section.cou (cross-section)

Written when `--cross-section` is active and a cross-section is defined.

Contains CFS in a vertical plane defined by the Cross section block in the
input file. Compatible with Coulomb 3.4 cross-section plotting.
