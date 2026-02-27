# OpenCoulomb

Open-source Python implementation of Coulomb failure stress computation, designed as a standalone replacement for the Coulomb 3.4 MATLAB package used in seismology research.

## Overview

OpenCoulomb computes Coulomb failure stress changes (CFS) caused by earthquake source faults on receiver faults or optimally oriented planes. It implements the Okada (1992) elastic dislocation model and supports the standard Coulomb 3.4 `.inp` file format for full compatibility with existing workflows.

## Installation

```bash
pip install opencoulomb
```

For development:

```bash
git clone https://github.com/opencoulomb/opencoulomb
cd opencoulomb
pip install -e ".[dev]"
```

## Quick Usage

### Command Line

```bash
# Compute CFS and write all output formats
opencoulomb compute input.inp -o output/ -f all

# Generate a CFS map
opencoulomb plot input.inp -o cfs_map.png -t cfs

# View model summary
opencoulomb info input.inp

# Validate an .inp file
opencoulomb validate input.inp

# Convert to a single format
opencoulomb convert input.inp -f csv -o results.csv
```

### Python API

```python
from opencoulomb.io import read_inp
from opencoulomb.core import compute_grid

model = read_inp("input.inp")
result = compute_grid(model)

# Access results
print(f"Peak CFS: {result.cfs.max():.4f} bar")
print(f"Grid shape: {result.grid_shape}")

# Write outputs
from opencoulomb.io import write_csv, write_dcff_cou
write_csv(result, "output.csv")
write_dcff_cou(result, model, "output_dcff.cou")

# Visualize
from opencoulomb.viz import plot_cfs_map, save_figure
fig, ax = plot_cfs_map(result, model)
save_figure(fig, "cfs_map.png")
```

## Features

- **Okada DC3D/DC3D0** — Vectorized NumPy implementation of the elastic dislocation model
- **Full .inp compatibility** — Parses all Coulomb 3.4 example files (23 tested)
- **CFS computation** — Specified receiver faults and optimally oriented planes (OOPs)
- **Cross-sections** — Vertical profile stress/displacement computation
- **Visualization** — CFS maps, fault traces, displacement quivers, cross-section plots
- **Multiple output formats** — Coulomb .cou, CSV, GMT .dat, text summary
- **CLI** — Five commands: `compute`, `plot`, `info`, `validate`, `convert`

## Requirements

- Python 3.10+
- NumPy >= 1.24
- SciPy >= 1.10
- Matplotlib >= 3.7
- Click >= 8.1

## Documentation

- [User Guide](docs/user/README.md) — Tutorials, how-to guides, reference, explanation
- [Architecture](docs/architecture/README.md) — Arc42 technical architecture
- [CLAUDE.md](CLAUDE.md) — LLM development guide

## Status

Alpha (v0.1.0) — Core computation engine complete. 811 tests, 95.9% coverage.

## License

Apache 2.0. See [LICENSE](LICENSE) for details.

## References

- Okada, Y. (1992). Internal deformation due to shear and tensile faults in a half-space. *Bulletin of the Seismological Society of America*, 82(2), 1018-1040.
- Lin, J., & Stein, R. S. (2004). Stress triggering in thrust and subduction earthquakes and stress interaction between the southern San Andreas and nearby thrust and strike-slip faults. *Journal of Geophysical Research*, 109(B2).
