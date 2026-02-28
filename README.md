# OpenCoulomb

Open-source Python implementation of Coulomb failure stress computation, designed as a standalone replacement for the Coulomb 3.4/4.0 MATLAB package used in seismology research.

## Overview

OpenCoulomb computes Coulomb failure stress changes (CFS) caused by earthquake source faults on receiver faults or optimally oriented planes. It implements the Okada (1992) elastic dislocation model and supports the standard Coulomb 3.4 `.inp` file format for full compatibility with existing workflows. Version 0.2.0 adds Coulomb 4.0 features including 3D volume computation, scaling relations, slip tapering, USGS finite fault import, earthquake catalog integration, and advanced visualization.

## Installation

```bash
pip install opencoulomb
```

For network features (USGS/ISC catalog queries, finite fault fetching):

```bash
pip install opencoulomb[network]
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

# 3D volume computation with slip tapering
opencoulomb compute input.inp --volume --depth-min 0 --depth-max 20 --depth-inc 2 --taper cosine

# Compute with strain output
opencoulomb compute input.inp --strain

# Scaling relations
opencoulomb scale 7.0 --type strike_slip --relation wells_coppersmith_1994

# Fetch USGS finite fault model
opencoulomb fetch us7000abcd

# Query earthquake catalog
opencoulomb catalog --start 2024-01-01 --end 2024-12-31 --min-mag 4.0

# Generate plots
opencoulomb plot input.inp -o cfs_map.png -t cfs
opencoulomb plot input.inp -t beachball --catalog catalog.csv
opencoulomb plot input.inp -t volume-slices --depth-min 0 --depth-max 20

# View model summary / validate
opencoulomb info input.inp
opencoulomb validate input.inp
```

### Python API

```python
from opencoulomb.io import read_inp
from opencoulomb.core import compute_grid, compute_volume

model = read_inp("input.inp")
result = compute_grid(model)

# Access results
print(f"Peak CFS: {result.cfs.max():.4f} bar")
print(f"Grid shape: {result.grid_shape}")

# 3D volume computation
from opencoulomb.types import VolumeGridSpec
vol_spec = VolumeGridSpec(-10, -10, 10, 10, 1.0, 1.0, 0.0, 20.0, 2.0)
volume = compute_volume(model, vol_spec)
cfs_3d = volume.cfs_volume()  # shape (n_z, n_y, n_x)

# Slip tapering
from opencoulomb.core import TaperSpec
result = compute_grid(model, taper=TaperSpec(n_along_strike=5, n_down_dip=3))

# Scaling relations
from opencoulomb.core import wells_coppersmith_1994, magnitude_to_fault
scaling = wells_coppersmith_1994(7.0)
print(f"Length: {scaling.length_km:.1f} km, Width: {scaling.width_km:.1f} km")

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

### Core (v0.1.0)
- **Okada DC3D/DC3D0** — Vectorized NumPy implementation of the elastic dislocation model
- **Full .inp compatibility** — Parses all Coulomb 3.4 example files (23 tested)
- **CFS computation** — Specified receiver faults and optimally oriented planes (OOPs)
- **Cross-sections** — Vertical profile stress/displacement computation
- **Visualization** — CFS maps, fault traces, displacement quivers, cross-section plots
- **Multiple output formats** — Coulomb .cou, CSV, GMT .dat, text summary
- **CLI** — Commands: `compute`, `plot`, `info`, `validate`, `convert`

### Coulomb 4.0 Features (v0.2.0)
- **3D volume grid** — Depth-loop engine for volumetric CFS computation
- **Scaling relations** — Wells & Coppersmith (1994) and Blaser et al. (2010)
- **Slip tapering** — Cosine, linear, elliptical edge taper profiles with fault subdivision
- **Strain output** — Full symmetric strain tensor alongside stress
- **USGS finite fault import** — Fetch earthquake models from USGS ComCat API
- **Earthquake catalogs** — ISC/USGS FDSN catalog queries via ObsPy
- **Beachball plots** — Focal mechanism visualization with CFS color overlay
- **GPS comparison** — Observed vs modeled displacement vectors with misfit statistics
- **3D visualization** — Depth slices, cross-sections, 3D scatter, animated GIFs

## Requirements

- Python 3.10+
- NumPy >= 1.24
- SciPy >= 1.10
- Matplotlib >= 3.7
- Click >= 8.1

Optional (for network features):
- ObsPy >= 1.4
- requests >= 2.28

## Documentation

- [User Guide](docs/user/README.md) — Tutorials, how-to guides, reference, explanation
- [Architecture](docs/architecture/README.md) — Arc42 technical architecture
- [CLAUDE.md](CLAUDE.md) — LLM development guide

## Status

v0.2.0 — Coulomb 4.0 feature parity. 1271 tests, 91% coverage.

## License

Apache 2.0. See [LICENSE](LICENSE) for details.

## References

- Okada, Y. (1992). Internal deformation due to shear and tensile faults in a half-space. *Bulletin of the Seismological Society of America*, 82(2), 1018-1040.
- Lin, J., & Stein, R. S. (2004). Stress triggering in thrust and subduction earthquakes and stress interaction between the southern San Andreas and nearby thrust and strike-slip faults. *Journal of Geophysical Research*, 109(B2).
- Wells, D. L., & Coppersmith, K. J. (1994). New empirical relationships among magnitude, rupture length, rupture width, rupture area, and surface displacement. *Bulletin of the Seismological Society of America*, 84(4), 974-1002.
- Blaser, L., et al. (2010). Scaling relations of earthquake source parameter estimates with special focus on subduction environment. *Bulletin of the Seismological Society of America*, 100(6), 2914-2926.
