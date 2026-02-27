# OpenCoulomb User Documentation

OpenCoulomb is a Python tool for computing **Coulomb failure stress (CFS)**
from fault dislocation models. It is a standalone replacement for the
Coulomb 3.4 MATLAB package.

## Quick links

- [Install OpenCoulomb](tutorials/installation.md)
- [Run your first computation](tutorials/quickstart.md)
- [CLI reference](reference/cli.md)

---

## Tutorials — learning-oriented

Start here if you are new to OpenCoulomb. Tutorials guide you through complete
worked examples step by step.

| Tutorial | What you will learn |
|----------|-------------------|
| [Installation](tutorials/installation.md) | Install via pip, verify the CLI works |
| [Quickstart](tutorials/quickstart.md) | Run a full CFS computation, examine outputs |
| [Visualization](tutorials/visualization.md) | Create CFS maps, displacement plots, cross-sections |

---

## How-to guides — task-oriented

Practical recipes for specific tasks. Assumes you are already familiar with
the basics.

| Guide | Task |
|-------|------|
| [Create an .inp file](how-to/create-inp-file.md) | Build or edit a Coulomb input file |
| [Batch processing](how-to/batch-processing.md) | Process many .inp files with shell scripts or Python |
| [Custom visualization](how-to/custom-visualization.md) | Change colormaps, export PDF/SVG, publication figures |

---

## Reference — information-oriented

Precise technical specifications. Use when you need to look up exact option
names, file formats, or function signatures.

| Reference | Contents |
|-----------|---------|
| [CLI reference](reference/cli.md) | All commands: compute, plot, info, validate, convert |
| [File formats](reference/file-formats.md) | .inp input format, .cou/.csv/.dat output formats |
| [API reference](reference/api.md) | Python functions: read_inp, compute_grid, write_csv, ... |

---

## Explanation — understanding-oriented

Background reading that explains *why* things work the way they do.

| Article | Topic |
|---------|-------|
| [Coulomb failure stress](explanation/coulomb-stress.md) | Theory, sign conventions, limitations |
| [Okada dislocation model](explanation/okada-model.md) | Elastic half-space, dc3d, superposition |

---

## Typical workflow

```bash
# 1. Inspect your model
opencoulomb info model.inp

# 2. Check for problems
opencoulomb validate model.inp

# 3. Compute
opencoulomb compute model.inp -o results/

# 4. Plot
opencoulomb plot model.inp -o results/cfs_map.png
```

Or in Python:

```python
from opencoulomb.io import read_inp
from opencoulomb.core import compute_grid
from opencoulomb.viz import plot_cfs_map, save_figure

model = read_inp("model.inp")
result = compute_grid(model)
fig, ax = plot_cfs_map(result, model, vmax=1.0)
save_figure(fig, "cfs_map.pdf")
```

---

## Getting help

- Open an issue on the [GitHub repository](https://github.com/opencoulomb/opencoulomb)
- Check the [CLI reference](reference/cli.md) for all available options
- See [Coulomb failure stress](explanation/coulomb-stress.md) for theory background
