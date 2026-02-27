# Tutorial: Installing OpenCoulomb

This tutorial walks you through installing OpenCoulomb and verifying it works correctly.

## Prerequisites

- Python 3.10 or later
- pip (comes with Python)

Check your Python version:

```bash
python --version
# Python 3.10.x or later required
```

## Install from PyPI

```bash
pip install opencoulomb
```

To install with optional visualization dependencies (required for the `plot` command):

```bash
pip install "opencoulomb[viz]"
```

## Install in a virtual environment (recommended)

Using a virtual environment avoids conflicts with other Python packages:

```bash
# Create environment
python -m venv .venv

# Activate it
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate.bat       # Windows

# Install
pip install "opencoulomb[viz]"
```

With [uv](https://docs.astral.sh/uv/) (faster alternative):

```bash
uv venv
source .venv/bin/activate
uv pip install "opencoulomb[viz]"
```

## Verify the installation

Run the built-in help to confirm the CLI is available:

```bash
opencoulomb --help
```

Expected output:

```
Usage: opencoulomb [OPTIONS] COMMAND [ARGS]...

  OpenCoulomb — Coulomb failure stress computation.

Options:
  --help  Show this message and exit.

Commands:
  compute   Compute Coulomb failure stress from an .inp file.
  convert   Convert an .inp file to a specific output format.
  info      Display model information from an .inp file.
  plot      Generate plots from an .inp file.
  validate  Validate an .inp file and report any issues.
```

Check the installed version:

```bash
opencoulomb --version
```

## Verify computation works

Download the [sample .inp file](../tutorials/quickstart.md#sample-input-file) and run:

```bash
opencoulomb validate sample.inp
```

You should see a summary like:

```
File: sample.inp
Model: Simple strike-slip earthquake

No issues found.

Summary: 1 source(s), 2 receiver(s), 10201 grid points
```

## Troubleshooting

**`opencoulomb: command not found`**

The pip install location is not on your `PATH`. Either activate your virtual
environment (see above) or use the module form:

```bash
python -m opencoulomb --help
```

**`ModuleNotFoundError: No module named 'matplotlib'`**

You installed the base package without visualization support. Fix with:

```bash
pip install "opencoulomb[viz]"
```

**Permission errors on Linux/macOS**

Never use `sudo pip install`. Use a virtual environment or the `--user` flag:

```bash
pip install --user "opencoulomb[viz]"
```

## Next steps

- [Quickstart tutorial](quickstart.md) — run your first computation
- [Visualization tutorial](visualization.md) — create CFS maps
