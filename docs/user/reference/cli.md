# CLI Reference

Complete reference for the `opencoulomb` command-line interface.

## Global options

```
opencoulomb [OPTIONS] COMMAND [ARGS]...
```

| Option | Description |
|--------|-------------|
| `--help` | Show help and exit |
| `--version` | Show version and exit |

---

## compute

Compute Coulomb failure stress from an `.inp` file. Writes output files to disk.

```
opencoulomb compute [OPTIONS] INP_FILE
```

### Arguments

| Argument | Description |
|----------|-------------|
| `INP_FILE` | Path to the `.inp` input file (must exist) |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output-dir PATH` | Same directory as input | Directory to write output files |
| `-f, --format [cou\|csv\|dat\|all]` | `all` | Output format(s); may be repeated |
| `--field [cfs\|shear\|normal]` | `cfs` | Stress field for `.dat` output |
| `--receiver INT` | All receivers | Receiver fault index (0-based) to resolve CFS onto |
| `--cross-section / --no-cross-section` | `--cross-section` | Compute cross-section if defined |
| `-v, --verbose` | False | Print progress messages |

### Output files

With `--format all` (default), all four files are written:

| File | Extension | Contents |
|------|-----------|----------|
| `{stem}_dcff.cou` | Coulomb 3.4 format | CFS grid, fault info |
| `{stem}.csv` | CSV with header | x, y, cfs, shear, normal, ux, uy, uz per grid point |
| `{stem}_{field}.dat` | Plain text grid | Single field for GMT or Python import |
| `{stem}_summary.txt` | Text | Peak values, model metadata |

Cross-section output (when `--cross-section` and cross-section defined):

| File | Extension | Contents |
|------|-----------|----------|
| `{stem}_section.cou` | Coulomb format | CFS in vertical plane |

### Examples

```bash
# Compute all outputs in same directory as input
opencoulomb compute model.inp

# Write to specific directory
opencoulomb compute model.inp -o results/model_run/

# Only write CSV output
opencoulomb compute model.inp -f csv -o results/

# Write CSV and COU, verbose
opencoulomb compute model.inp -f csv -f cou -v

# Resolve CFS onto second receiver fault
opencoulomb compute model.inp --receiver 1

# Shear stress .dat output
opencoulomb compute model.inp --field shear
```

---

## plot

Generate a plot from an `.inp` file. Computes CFS internally.

```
opencoulomb plot [OPTIONS] INP_FILE
```

### Arguments

| Argument | Description |
|----------|-------------|
| `INP_FILE` | Path to the `.inp` input file (must exist) |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output PATH` | `{stem}_{type}.png` | Output image path |
| `-t, --type [cfs\|displacement\|section]` | `cfs` | Plot type |
| `--vmax FLOAT` | Auto (98th percentile) | Symmetric color scale maximum |
| `--dpi INT` | `300` | Output resolution in dots per inch |
| `--no-faults` | False | Hide fault trace overlays |
| `--receiver INT` | First receiver | Receiver fault index (0-based) |
| `-v, --verbose` | False | Print progress messages |

### Plot types

| Type | Description | Requires |
|------|-------------|---------|
| `cfs` | Horizontal CFS map at grid depth | — |
| `displacement` | Three-panel ux/uy/uz displacement | — |
| `section` | Vertical CFS cross-section | Cross-section block in `.inp` |

### Output formats

Inferred from the file extension of `--output`:

| Extension | Format |
|-----------|--------|
| `.png` | PNG raster |
| `.pdf` | PDF vector |
| `.svg` | SVG vector |
| `.eps` | EPS vector |

### Examples

```bash
# Default CFS map at 300 DPI
opencoulomb plot model.inp

# Save to specific path
opencoulomb plot model.inp -o figures/model_cfs.pdf

# Displacement plot
opencoulomb plot model.inp -t displacement -o displacement.png

# Cross-section
opencoulomb plot model.inp -t section -o section.png

# Fixed color scale at ±1 bar
opencoulomb plot model.inp --vmax 1.0

# Draft resolution, no faults
opencoulomb plot model.inp --dpi 100 --no-faults -o draft.png

# Select receiver fault 1
opencoulomb plot model.inp --receiver 1 -o cfs_receiver1.png
```

---

## info

Display model metadata from an `.inp` file. Does not compute CFS.

```
opencoulomb info INP_FILE
```

### Arguments

| Argument | Description |
|----------|-------------|
| `INP_FILE` | Path to the `.inp` input file |

### Output fields

- Model title
- Material: Poisson's ratio, Young's modulus, friction coefficient
- Grid bounds, spacing, depth, total point count
- Source faults: strike, dip, slip components
- Receiver faults: strike, dip
- Regional stress (if defined)
- Cross-section bounds and depth range (if defined)

### Example

```bash
opencoulomb info northridge.inp
```

```
Model: 1994 Northridge earthquake
Material: Poisson=0.2500, Young=800000 bar, friction=0.4000
Grid: X=[-80.00, 80.00], Y=[-80.00, 80.00]
  Spacing: 2.0000 x 2.0000 km, Depth: 10.00 km
  Points: 81 x 81 = 6561
Faults: 1 source(s), 2 receiver(s)
  [0] Main thrust: strike=122.0, dip=40.0, slip=(0.000, 1.800) m
  [0] Aftershock zone N: strike=120.0, dip=55.0
  [1] Aftershock zone S: strike=118.0, dip=42.0
Cross-section: (-20.0, 0.0) to (20.0, 0.0), depth 0.0-30.0 km
```

---

## validate

Check an `.inp` file for issues without computing. Parse errors cause a non-zero
exit code; warnings are printed but exit is 0.

```
opencoulomb validate [OPTIONS] INP_FILE
```

### Arguments

| Argument | Description |
|----------|-------------|
| `INP_FILE` | Path to the `.inp` input file |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-v, --verbose` | False | Print detailed progress |

### Checks performed

| Check | Condition |
|-------|-----------|
| Parse success | File can be read without errors |
| Source faults | At least one fault has non-zero slip |
| Receiver faults | At least one receiver defined |
| Grid size | Warns if >1,000,000 points |
| Grid depth | Warns if depth is negative |
| Fault geometry | Warns on zero-length faults |
| Fault depth | Warns if bottom depth >100 km |
| Cross-section | Warns if depth_max >100 km |

### Examples

```bash
opencoulomb validate model.inp

# Validate multiple files
for f in models/*.inp; do opencoulomb validate "$f"; done

# Use exit code in scripts
opencoulomb validate model.inp && echo "OK" || echo "FAILED"
```

---

## convert

Compute CFS and write a single output file in the specified format.
Equivalent to `compute` restricted to one format.

```
opencoulomb convert [OPTIONS] INP_FILE
```

### Arguments

| Argument | Description |
|----------|-------------|
| `INP_FILE` | Path to the `.inp` input file |

### Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `-f, --format [cou\|csv\|dat\|summary]` | Yes | — | Output format |
| `-o, --output PATH` | No | Auto | Output file path |
| `--field [cfs\|shear\|normal]` | No | `cfs` | Field for `.dat` format |
| `--receiver INT` | No | All | Receiver fault index |
| `-v, --verbose` | No | False | Verbose output |

### Default output paths

| Format | Default path |
|--------|-------------|
| `cou` | `{stem}_dcff.cou` |
| `csv` | `{stem}.csv` |
| `dat` | `{stem}_{field}.dat` |
| `summary` | `{stem}_summary.txt` |

### Examples

```bash
# Export CSV
opencoulomb convert model.inp -f csv

# Export to specific path
opencoulomb convert model.inp -f csv -o /data/results/model.csv

# Export normal stress .dat
opencoulomb convert model.inp -f dat --field normal

# Export summary text
opencoulomb convert model.inp -f summary
```
