# Tutorial: Your First Computation

This tutorial runs a complete Coulomb failure stress computation from start to finish.
By the end you will have output files and understand the basic workflow.

## What you will do

1. Create a sample input file
2. Inspect the model
3. Compute CFS
4. Look at the outputs

## Sample input file

Create a file called `strike_slip.inp` with this content:

```
Simple strike-slip earthquake
OpenCoulomb quickstart example
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

  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot
 xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx
    2    -30.000    10.000     30.000    10.000  100      0.000     0.000    90.000     0.000    15.000  North receiver
    3    -30.000   -10.000     30.000   -10.000  100      0.000     0.000    90.000     0.000    15.000  South receiver

Grid Parameters
  1  ---  Start-x =    -100.000
  2  ---  Start-y =    -100.000
  3  ---  Finish-x =    100.000
  4  ---  Finish-y =    100.000
  5  ---  x-increment =   2.000
  6  ---  y-increment =   2.000
```

This models a 40 km long, 15 km deep right-lateral strike-slip fault with two
parallel receiver faults, evaluated on a 100 x 100 point grid at 10 km depth.

## Step 1: Inspect the model

Before computing, check that the file is valid:

```bash
opencoulomb info strike_slip.inp
```

Output:

```
Model: Simple strike-slip earthquake
Material: Poisson=0.2500, Young=800000 bar, friction=0.4000
Grid: X=[-100.00, 100.00], Y=[-100.00, 100.00]
  Spacing: 2.0000 x 2.0000 km, Depth: 10.00 km
  Points: 101 x 101 = 10201
Faults: 1 source(s), 2 receiver(s)
  [0] Main fault: strike=90.0, dip=90.0, slip=(1.000, 0.000) m
  [0] North receiver: strike=90.0, dip=90.0
  [1] South receiver: strike=90.0, dip=90.0
```

## Step 2: Validate

```bash
opencoulomb validate strike_slip.inp
```

```
File: strike_slip.inp
Model: Simple strike-slip earthquake

No issues found.

Summary: 1 source(s), 2 receiver(s), 10201 grid points
```

## Step 3: Compute

```bash
opencoulomb compute strike_slip.inp -o results/
```

```
Done. Output in results/
```

With verbose output to see progress:

```bash
opencoulomb compute strike_slip.inp -o results/ -v
```

```
INFO Parsing strike_slip.inp
INFO Model: Simple strike-slip earthquake (1 sources, 2 receivers)
INFO Computing grid CFS...
INFO Grid: 101 x 101 points
INFO Wrote strike_slip_dcff.cou
INFO Wrote strike_slip.csv
INFO Wrote strike_slip_cfs.dat
INFO Wrote strike_slip_summary.txt
Done. Output in results/
```

## Step 4: Examine the outputs

The `results/` directory contains:

| File | Description |
|------|-------------|
| `strike_slip_dcff.cou` | Coulomb-format CFS grid (compatible with Coulomb 3.4) |
| `strike_slip.csv` | Grid data as CSV (x, y, cfs, shear, normal) |
| `strike_slip_cfs.dat` | Plain text grid for GMT / Python import |
| `strike_slip_summary.txt` | Text summary with peak CFS values |

Inspect the summary:

```bash
cat results/strike_slip_summary.txt
```

The CSV file has a header row and one row per grid point:

```
x_km,y_km,cfs_bar,shear_bar,normal_bar,ux_m,uy_m,uz_m
-100.0,-100.0,...
```

## Step 5: Quick plot

```bash
opencoulomb plot strike_slip.inp -o results/cfs_map.png
```

Opens `results/cfs_map.png` — a color map of CFS with fault traces overlaid.
Red areas are stress-increased (promoted failure), blue are stress-decreased.

## Understanding the result

- **Positive CFS** (red): stress brought closer to failure; aftershocks more likely
- **Negative CFS** (blue): stress moved away from failure; region is stress-shadowed
- Lobes appear off each end of the fault ("stress shadows" along strike) and at the
  fault tips ("stress concentrations" perpendicular to strike) — this is the classic
  strike-slip CFS pattern

## Next steps

- [Visualization tutorial](visualization.md) — customize maps and cross-sections
- [Create an .inp file](../how-to/create-inp-file.md) — build your own model
- [CLI reference](../reference/cli.md) — all compute options
