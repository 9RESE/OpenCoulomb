# How to Create an .inp Input File

This guide explains how to build a Coulomb `.inp` input file from scratch.
An `.inp` file defines the fault geometry, material properties, grid, and
regional stress for a CFS computation.

## File structure overview

An `.inp` file has four mandatory sections in order:

1. **Header** — two free-text comment lines
2. **Material parameters** — elastic moduli, friction, regional stress
3. **Fault table(s)** — one or more blocks of fault geometry + slip
4. **Grid parameters** — computation grid extent and spacing

Optional sections: Size Parameters, Cross section default.

## Minimal example

```
My earthquake model
Created 2026-01-15
#reg1=  0  #reg2=  0  #fixed=  1  sym=  1
 PR1=       0.250 PR2=       0.250 DEPTH=      10.000
  E1=  0.800000E+06  E2=  0.800000E+06 XLIM=     0.000 YLIM=     0.000
FRIC=       0.400
  S1DR=  189.0000 S1DP=   -0.0001 S1IN=  100.000  S1GD=   0.000
  S3DR=   99.0000 S3DP=    0.0000 S3IN=    0.000  S3GD=   0.000
  S2DR=  270.0001 S2DP=  -89.999  S2IN=    0.000  S2GD=   0.000

  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot
 xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx
    1    -20.000     0.000     20.000     0.000  100      1.000     0.000    90.000     0.000    15.000  Main fault

Grid Parameters
  1  ---  Start-x =    -100.000
  2  ---  Start-y =    -100.000
  3  ---  Finish-x =    100.000
  4  ---  Finish-y =    100.000
  5  ---  x-increment =   2.000
  6  ---  y-increment =   2.000
```

## Section 1: Header

The first two lines are free text. Use them to describe the model:

```
1994 Northridge earthquake — main shock
Model: uniform slip, Poisson solid
```

## Section 2: Material parameters

```
#reg1=  0  #reg2=  0  #fixed=  1  sym=  1
 PR1=       0.250 PR2=       0.250 DEPTH=      10.000
  E1=  0.800000E+06  E2=  0.800000E+06 XLIM=     0.000 YLIM=     0.000
FRIC=       0.400
```

| Parameter | Meaning | Typical value |
|-----------|---------|---------------|
| `PR1`, `PR2` | Poisson's ratio | 0.25 (Poisson solid) |
| `DEPTH` | Default grid depth (km) | 5–20 |
| `E1`, `E2` | Young's modulus (bar) | 8×10⁵ |
| `XLIM`, `YLIM` | Symmetry axes (0 = none) | 0.000 |
| `FRIC` | Coefficient of friction | 0.4 |

### Regional stress (S1/S2/S3)

The three principal stress axes are defined by direction (`DR`), plunge (`DP`),
magnitude (`IN` in bar), and gradient (`GD` in bar/km):

```
  S1DR=  189.0000 S1DP=   -0.0001 S1IN=  100.000  S1GD=   0.000
  S3DR=   99.0000 S3DP=    0.0000 S3IN=    0.000  S3GD=   0.000
  S2DR=  270.0001 S2DP=  -89.999  S2IN=    0.000  S2GD=   0.000
```

For a strike-slip regime with NNE compression, S1 is horizontal (~N9E),
S3 horizontal (~E), and S2 vertical. Set all to zero for no regional stress.

## Section 3: Fault table

Each fault table block starts with a two-line header (comment + format string)
followed by one line per fault:

```
  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot
 xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx
    1    -20.000     0.000     20.000     0.000  100      1.000     0.000    90.000     0.000    15.000  Main fault
```

### Fault columns

| Column | Meaning | Unit |
|--------|---------|------|
| Index | Row number (not used internally) | — |
| X-start, Y-start | Surface trace start (km) | km |
| X-fin, Y-fin | Surface trace end (km) | km |
| Kode | Fault type code | integer |
| rt.lat | Right-lateral slip | m |
| reverse | Reverse (thrust) slip | m |
| dip | Dip angle from horizontal | degrees |
| top | Top depth | km |
| bot | Bottom depth | km |
| Label | Optional text label | — |

### Kode values

| Kode | Meaning |
|------|---------|
| 100 | Standard dislocation |
| 200 | Tensile (opening) crack |
| 300 | Magmatic intrusion |
| 400 | Pressurized ellipsoid |
| 500 | Point source |

### Source vs receiver faults

Faults with non-zero slip (`rt.lat` or `reverse` non-zero) are **source faults**.
Faults with zero slip are **receiver faults** — CFS is resolved onto their plane.

Use separate table blocks (each with its own header) to group sources and receivers:

```
  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot
 xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx
    1    -20.000     0.000     20.000     0.000  100      1.000     0.000    90.000     0.000    15.000  Main fault

  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot
 xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx
    2    -30.000    10.000     30.000    10.000  100      0.000     0.000    90.000     0.000    15.000  Receiver
```

## Section 4: Grid parameters

```
Grid Parameters
  1  ---  Start-x =    -100.000
  2  ---  Start-y =    -100.000
  3  ---  Finish-x =    100.000
  4  ---  Finish-y =    100.000
  5  ---  x-increment =   2.000
  6  ---  y-increment =   2.000
```

The grid is computed at the depth set in `DEPTH` (material parameters section).
Choose increment to balance resolution and compute time:

| Grid size | Increment | Points | Compute time |
|-----------|-----------|--------|--------------|
| 200×200 km | 2 km | 101×101 ≈ 10 k | <1 s |
| 200×200 km | 1 km | 201×201 ≈ 40 k | ~1 s |
| 200×200 km | 0.5 km | 401×401 ≈ 160 k | ~5 s |

## Optional: Cross section

Append after Grid Parameters to enable vertical profiles:

```
   Cross section default
  1  ---  Start-x =    0.000
  2  ---  Start-y =    0.000
  3  ---  Finish-x =    0.000
  4  ---  Finish-y =   50.000
  5  ---  Distant-increment =   1.000
  6  ---  Z-depth =   -30.000
  7  ---  Z-increment =    1.000
```

## Validate your file

After writing the file, always validate before computing:

```bash
opencoulomb validate mymodel.inp
```

Check for warnings about zero-length faults, extreme depths, or very large grids.

## Common mistakes

**Wrong slip units** — slip must be in metres, not centimetres.

**Depth sign convention** — `top` and `bot` are positive downward (km below surface).
A fault from surface to 15 km depth: `top=0.000 bot=15.000`.

**Receiver fault slip** — set both `rt.lat` and `reverse` to exactly `0.000`
for receiver faults. Any non-zero value makes the fault a source.

**Grid too coarse** — increment larger than fault length gives poor resolution.
Use increment ≤ fault length / 10 for meaningful results.
