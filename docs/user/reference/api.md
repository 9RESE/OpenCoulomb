# Python API Reference

Public Python API for OpenCoulomb. All functions are importable from the
top-level subpackages.

---

## I/O — `opencoulomb.io`

### `read_inp`

```python
from opencoulomb.io import read_inp
```

```python
def read_inp(path: str | Path) -> CoulombModel
```

Parse a Coulomb `.inp` file and return a fully populated model.

**Parameters**

| Name | Type | Description |
|------|------|-------------|
| `path` | `str` or `Path` | Path to the `.inp` file |

**Returns** `CoulombModel` — immutable dataclass with all model data.

**Raises** `ParseError` if the file cannot be read or is malformed.

**Example**

```python
from opencoulomb.io import read_inp

model = read_inp("northridge.inp")
print(model.title)                    # "1994 Northridge earthquake"
print(model.n_sources)                # 1
print(model.n_receivers)              # 3
print(model.material.friction)        # 0.4
print(model.grid.depth)               # 10.0  (km)
```

---

### `parse_inp_string`

```python
from opencoulomb.io import parse_inp_string
```

```python
def parse_inp_string(text: str) -> CoulombModel
```

Parse `.inp` content from a string. Useful for testing or in-memory processing.

**Example**

```python
inp_text = open("model.inp").read()
model = parse_inp_string(inp_text)
```

---

### `write_csv`

```python
from opencoulomb.io import write_csv
```

```python
def write_csv(result: CoulombResult, path: str | Path) -> None
```

Write computation results to a CSV file with columns:
`x_km, y_km, cfs_bar, shear_bar, normal_bar, ux_m, uy_m, uz_m`.

---

### `write_dcff_cou`

```python
from opencoulomb.io import write_dcff_cou
```

```python
def write_dcff_cou(result: CoulombResult, model: CoulombModel, path: str | Path) -> None
```

Write CFS results in Coulomb 3.4 `.cou` format. Compatible with Coulomb's
plotting tools.

---

### `write_coulomb_dat`

```python
from opencoulomb.io import write_coulomb_dat
```

```python
def write_coulomb_dat(
    result: CoulombResult,
    path: str | Path,
    field: str = "cfs",
) -> None
```

Write a single stress field as a plain text grid (x, y, value per line).

**Parameters**

| Name | Type | Values | Description |
|------|------|--------|-------------|
| `field` | `str` | `"cfs"`, `"shear"`, `"normal"` | Field to write |

---

### `write_summary`

```python
from opencoulomb.io import write_summary
```

```python
def write_summary(result: CoulombResult, model: CoulombModel, path: str | Path) -> None
```

Write a human-readable summary text file with peak values and model metadata.

---

## Core — `opencoulomb.core`

### `compute_grid`

```python
from opencoulomb.core import compute_grid
```

```python
def compute_grid(
    model: CoulombModel,
    receiver_index: int | None = None,
) -> CoulombResult
```

Run the full CFS computation on the model's observation grid.

The pipeline:
1. Generate observation grid from `model.grid`
2. For each source fault: compute Okada displacements and stress (superposition)
3. Resolve total stress onto the receiver fault — compute CFS
4. If `model.regional_stress` is set: compute optimally oriented planes (OOPs)

**Parameters**

| Name | Type | Description |
|------|------|-------------|
| `model` | `CoulombModel` | Parsed model |
| `receiver_index` | `int` or `None` | Which receiver fault to use (0-based). `None` = first receiver, or first source fault if no receivers defined |

**Returns** `CoulombResult`

**Raises**

| Exception | Condition |
|-----------|-----------|
| `ComputationError` | Model has no source faults |
| `ValidationError` | `receiver_index` out of range |

**Example**

```python
from opencoulomb.io import read_inp
from opencoulomb.core import compute_grid

model = read_inp("model.inp")
result = compute_grid(model)

# Access flat arrays (shape: n_points,)
print(result.cfs.max())       # max CFS in bar
print(result.shear.min())

# Reshape to 2D grid (n_y, n_x)
cfs_2d = result.cfs_grid()

# Displacement grids
ux_2d, uy_2d, uz_2d = result.displacement_grid()
```

---

### `compute_cross_section`

```python
from opencoulomb.core import compute_cross_section
```

```python
def compute_cross_section(
    model: CoulombModel,
    spec: CrossSectionSpec | None = None,
    receiver_index: int | None = None,
) -> CrossSectionResult
```

Compute stress and CFS on a vertical profile.

**Parameters**

| Name | Type | Description |
|------|------|-------------|
| `model` | `CoulombModel` | Parsed model |
| `spec` | `CrossSectionSpec` or `None` | Override cross-section geometry; uses `model.cross_section` if `None` |
| `receiver_index` | `int` or `None` | Receiver fault index for CFS resolution |

**Returns** `CrossSectionResult` with attributes:
- `distance` — along-profile distances (km), shape `(n_horiz,)`
- `depth` — depth values (km), shape `(n_vert,)`
- `cfs`, `shear`, `normal` — stress fields, shape `(n_vert, n_horiz)`

**Raises** `ComputationError` if no cross-section spec is available.

**Example**

```python
from opencoulomb.core import compute_cross_section

section = compute_cross_section(model)
print(section.cfs.shape)     # (n_vert, n_horiz)
print(section.depth.max())   # maximum depth (km)
```

---

### `compute_element_cfs`

```python
from opencoulomb.core import compute_element_cfs
```

```python
def compute_element_cfs(model: CoulombModel) -> ElementResult | None
```

Compute CFS at the center of each receiver fault element, using each
receiver's own orientation for resolution.

Returns `None` if the model has no receiver faults.

**Example**

```python
from opencoulomb.core import compute_element_cfs

element_result = compute_element_cfs(model)
if element_result is not None:
    for fault, cfs_val in zip(element_result.elements, element_result.cfs):
        print(f"{fault.label}: {cfs_val:.4f} bar")
```

---

### `compute_cfs`

```python
from opencoulomb.core import compute_cfs
```

```python
def compute_cfs(
    shear: NDArray,
    normal: NDArray,
    friction: float,
) -> NDArray
```

Apply the Coulomb failure criterion: `CFS = shear + friction * normal`.

---

### `dc3d`

```python
from opencoulomb.core import dc3d
```

```python
def dc3d(
    alpha: float,
    x: NDArray, y: NDArray, z: NDArray,
    depth: float,
    dip: float,
    al1: float, al2: float,
    aw1: float, aw2: float,
    disl1: float, disl2: float, disl3: float,
) -> tuple[NDArray, ...]
```

Okada (1992) displacement and displacement gradient for a finite rectangular
fault. Returns a 12-element tuple: `(ux, uy, uz, uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz)`.

---

## Data types — `opencoulomb.types`

### `CoulombModel`

Frozen dataclass. Key attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `title` | `str` | First line of `.inp` file |
| `material` | `MaterialProps` | Elastic/friction parameters |
| `grid` | `GridSpec` | Observation grid specification |
| `faults` | `list[FaultElement]` | All faults (sources + receivers) |
| `source_faults` | `list[FaultElement]` | Faults with non-zero slip |
| `receiver_faults` | `list[FaultElement]` | Faults with zero slip |
| `n_sources` | `int` | Number of source faults |
| `n_receivers` | `int` | Number of receiver faults |
| `regional_stress` | `RegionalStress \| None` | Principal stress axes |
| `cross_section` | `CrossSectionSpec \| None` | Vertical profile parameters |

### `CoulombResult`

Frozen dataclass returned by `compute_grid`. Key attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `stress` | `StressResult` | Raw stress tensor and displacement (flat arrays) |
| `cfs` | `NDArray` shape `(N,)` | CFS values in bar |
| `shear` | `NDArray` shape `(N,)` | Shear stress in bar |
| `normal` | `NDArray` shape `(N,)` | Normal stress in bar |
| `grid_shape` | `tuple[int, int]` | `(n_y, n_x)` for reshaping |
| `receiver_strike` | `float` | Degrees |
| `receiver_dip` | `float` | Degrees |
| `receiver_rake` | `float` | Degrees |
| `oops_strike/dip/rake` | `NDArray \| None` | Optimal planes (if regional stress set) |

Methods:

| Method | Returns | Description |
|--------|---------|-------------|
| `cfs_grid()` | `NDArray (n_y, n_x)` | CFS reshaped to 2D |
| `displacement_grid()` | `tuple of NDArray` | ux, uy, uz each `(n_y, n_x)` |

---

## Visualization — `opencoulomb.viz`

### `plot_cfs_map`

```python
from opencoulomb.viz import plot_cfs_map
```

```python
def plot_cfs_map(
    result: CoulombResult,
    model: CoulombModel,
    vmax: float | None = None,
    show_faults: bool = True,
) -> tuple[Figure, Axes]
```

### `plot_displacement`

```python
from opencoulomb.viz import plot_displacement
```

```python
def plot_displacement(
    result: CoulombResult,
    model: CoulombModel,
    show_faults: bool = True,
) -> tuple[Figure, list[Axes]]
```

Returns a three-panel figure with east, north, and vertical displacement.

### `plot_cross_section`

```python
from opencoulomb.viz import plot_cross_section
```

```python
def plot_cross_section(
    section: CrossSectionResult,
    vmax: float | None = None,
) -> tuple[Figure, Axes]
```

### `save_figure`

```python
from opencoulomb.viz import save_figure
```

```python
def save_figure(fig: Figure, path: str | Path, dpi: int = 300) -> None
```

Save a Matplotlib figure. Format inferred from the path extension.
Closes the figure after saving.
