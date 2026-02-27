# Arc42 § 7 — Deployment

## 7.1 Distribution Model

OpenCoulomb is distributed as a pure Python wheel on PyPI. There are no compiled extensions, so the same wheel installs on Linux, macOS, and Windows without a build step.

```
PyPI: pip install opencoulomb
```

The package ships:
- The `opencoulomb` importable package (under `src/`)
- The `opencoulomb` CLI entry point (registered via `pyproject.toml` `[project.scripts]`)

## 7.2 Runtime Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.10, 3.11, 3.12 |
| NumPy | ≥ 1.24 |
| SciPy | ≥ 1.10 |
| Matplotlib | ≥ 3.7 |
| Click | ≥ 8.1 |

No C compiler, Fortran compiler, or MATLAB installation is required.

## 7.3 Installation Scenarios

### Scientist's laptop (standard)

```bash
pip install opencoulomb
opencoulomb --version
opencoulomb compute model.inp --output ./results/
```

### Virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install opencoulomb
```

### conda / mamba environment

```bash
conda create -n coulomb python=3.12
conda activate coulomb
pip install opencoulomb           # PyPI; not yet on conda-forge
```

### Development installation

```bash
git clone https://github.com/<org>/opencoulomb
cd opencoulomb
pip install -e ".[dev]"           # installs test deps (pytest, coverage, ruff)
pytest                             # run full test suite
```

Build system uses **hatchling** with `pyproject.toml`; no `setup.py`.

## 7.4 Docker (Analysis Environment)

For reproducible batch runs or HPC cluster use:

```dockerfile
FROM python:3.12-slim
RUN pip install opencoulomb
ENTRYPOINT ["opencoulomb"]
```

```bash
docker build -t opencoulomb .
docker run --rm -v $(pwd):/data opencoulomb compute /data/model.inp --output /data/results/
```

## 7.5 File System Layout (Runtime)

```
~/ or project dir
├── model.inp            ← Input: Coulomb 3.4 .inp file
└── results/             ← Output directory (user-specified)
    ├── cfs.csv          ← Grid CFS values (x, y, cfs_bar, ...)
    ├── cfs.dat          ← Coulomb-compatible space-delimited
    ├── cfs.cou          ← Coulomb 3.4 output format
    └── cfs_map.png      ← CFS map figure
```

OpenCoulomb writes **no configuration files** to the user's home directory.
All output paths are explicit CLI arguments (`--output`).

## 7.6 PyPI Release Process

```
1. Bump version in pyproject.toml
2. git tag v0.x.y
3. CI (GitHub Actions) runs:
   a. pytest (Linux, macOS, Windows × Python 3.10/3.11/3.12)
   b. coverage check (≥ 90%)
   c. ruff lint
   d. hatchling build → sdist + wheel
   e. twine upload to PyPI (on tag)
```

## 7.7 No Server-Side Components

OpenCoulomb is a **desktop / batch** tool. There is no:
- Web server or API endpoint
- Database
- Background daemon or service
- Network dependency at runtime

All computations run locally and offline.
