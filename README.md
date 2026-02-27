# OpenCoulomb

Open-source Python implementation of Coulomb failure stress computation, designed as a standalone replacement for the Coulomb 3.4 MATLAB package used in seismology research.

## Overview

OpenCoulomb computes Coulomb failure stress changes (ΔCFS) caused by earthquake source faults on receiver faults. It implements the Okada (1992) elastic dislocation model and supports the standard Coulomb 3.4 `.inp` file format for compatibility with existing workflows.

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
opencoulomb compute input.inp
```

Output files are written to the same directory as the input by default.

### Python API

```python
import opencoulomb

model = opencoulomb.load("input.inp")
result = opencoulomb.compute(model)
result.plot()
result.save("output/")
```

## Requirements

- Python 3.10+
- NumPy >= 1.24
- SciPy >= 1.10
- Matplotlib >= 3.7
- Click >= 8.1

## Status

Alpha — core computation engine under active development.

## License

Apache 2.0. See [LICENSE](LICENSE) for details.

## References

- Okada, Y. (1992). Internal deformation due to shear and tensile faults in a half-space. *Bulletin of the Seismological Society of America*, 82(2), 1018-1040.
- Lin, J., & Stein, R. S. (2004). Stress triggering in thrust and subduction earthquakes and stress interaction between the southern San Andreas and nearby thrust and strike-slip faults. *Journal of Geophysical Research*, 109(B2).
