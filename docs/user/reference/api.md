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

**Raises**

| Exception | Condition |
|-----------|-----------|
| `ParseError` | File is malformed or cannot be parsed |
| `InputError` | File cannot be opened (permissions, missing) |

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
| `field` | `str` | `"cfs"`, `"shear"`, `"normal"`, `"ux"`, `"uy"`, `"uz"` | Field to write |

**Raises** `OutputError` if the file cannot be written. `ValueError` if `field` is invalid.

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

### Exceptions

All exceptions are importable from the top-level package:

```python
from opencoulomb import ParseError, InputError, OutputError, ComputationError, ValidationError
```

| Exception | Base | Raised by |
|-----------|------|-----------|
| `OpenCoulombError` | `Exception` | Base for all library errors |
| `InputError` | `OpenCoulombError` | File open failures in `read_inp` |
| `ParseError` | `InputError` | Malformed `.inp` content |
| `FormatError` | `InputError` | Unsupported file format |
| `ValidationError` | `OpenCoulombError` | Invalid parameters (grid, faults, material) |
| `ConfigError` | `OpenCoulombError` | Configuration issues |
| `ComputationError` | `OpenCoulombError` | Runtime computation failures |
| `SingularityError` | `ComputationError` | Numerical singularity |
| `ConvergenceError` | `ComputationError` | Iterative convergence failure |
| `OutputError` | `OpenCoulombError` | File write failures |

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

### Coordinate utilities

All coordinate functions are exported from `opencoulomb.core`:

```python
from opencoulomb.core import (
    compute_fault_geometry,
    direction_cosines,
    fault_to_geo_displacement,
    geo_to_fault,
    rotation_matrix,
    strike_dip_to_normal,
)
```

| Function | Purpose |
|----------|---------|
| `compute_fault_geometry(fault)` | Fault element → Okada geometry dict |
| `direction_cosines(strike_rad, dip_rad)` | Fault-local unit vectors (Okada convention) |
| `fault_to_geo_displacement(...)` | Fault-local → geographic displacement |
| `geo_to_fault(...)` | Geographic → fault-local coordinates |
| `rotation_matrix(strike_rad, dip_rad)` | 3x3 rotation matrix fault↔geographic |
| `strike_dip_to_normal(strike_rad, dip_rad)` | Unit normal to fault plane |

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

---

## Core — v0.2.0 Additions

### `compute_volume`

```python
from opencoulomb.core import compute_volume
```

```python
def compute_volume(
    model: CoulombModel,
    volume_spec: VolumeGridSpec,
    receiver_index: int | None = None,
    compute_strain: bool = False,
    taper: TaperSpec | None = None,
) -> VolumeResult
```

Run 3D CFS computation through depth layers defined by `volume_spec`.

**Parameters**

| Name | Type | Description |
|------|------|-------------|
| `model` | `CoulombModel` | Parsed model |
| `volume_spec` | `VolumeGridSpec` | 3D grid bounds and depth range |
| `receiver_index` | `int` or `None` | Receiver fault for CFS resolution |
| `compute_strain` | `bool` | Also compute strain tensor |
| `taper` | `TaperSpec` or `None` | Optional slip taper specification |

**Returns** `VolumeResult`

**Example**

```python
from opencoulomb.types import VolumeGridSpec
from opencoulomb.core import compute_volume

spec = VolumeGridSpec(-10, -10, 10, 10, 1.0, 1.0, 0.0, 20.0, 2.0)
volume = compute_volume(model, spec)
cfs_3d = volume.cfs_volume()        # shape (n_z, n_y, n_x)
slice_2d = volume.slice_at_depth(5)  # CoulombResult at depth index 5
```

---

### `gradients_to_strain`

```python
from opencoulomb.core import gradients_to_strain
```

```python
def gradients_to_strain(
    uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz
) -> tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray]
```

Convert displacement gradients to symmetric strain tensor components.
Returns `(exx, eyy, ezz, eyz, exz, exy)`.

---

### Scaling relations

```python
from opencoulomb.core import wells_coppersmith_1994, blaser_2010, magnitude_to_fault
```

| Function | Returns | Description |
|----------|---------|-------------|
| `wells_coppersmith_1994(magnitude, fault_type)` | `ScalingResult` | WC94 scaling |
| `blaser_2010(magnitude, fault_type)` | `ScalingResult` | Blaser 2010 scaling |
| `magnitude_to_fault(magnitude, center_x, center_y, ...)` | `FaultElement` | Create fault from magnitude |

`ScalingResult` has attributes: `length_km`, `width_km`, `area_km2`, `displacement_m`, `magnitude`, `fault_type`, `relation`.

---

### Slip tapering

```python
from opencoulomb.core import TaperSpec, TaperProfile, subdivide_and_taper
```

| Function | Description |
|----------|-------------|
| `subdivide_fault(fault, n_strike, n_dip)` | Tile fault into sub-patches |
| `apply_taper(subfaults, taper_spec)` | Apply slip taper to sub-patches |
| `subdivide_and_taper(fault, taper)` | Combined one-step function |

`TaperProfile` enum: `COSINE`, `LINEAR`, `ELLIPTICAL`

---

## I/O — v0.2.0 Additions

### Volume writers

```python
from opencoulomb.io import write_volume_csv, write_volume_slices
```

| Function | Description |
|----------|-------------|
| `write_volume_csv(volume, path)` | 15-column CSV with depth column |
| `write_volume_slices(volume, output_dir, field)` | One `.dat` file per depth |

### USGS client

```python
from opencoulomb.io import search_events, fetch_coulomb_inp, fetch_finite_fault
```

Requires `opencoulomb[network]`. Functions query the USGS ComCat API.

### Catalog I/O

```python
from opencoulomb.io import read_catalog_csv, write_catalog_csv
```

### GPS reader

```python
from opencoulomb.io import read_gps_csv, read_gps_json
```

---

## Visualization — v0.2.0 Additions

### Volume plots

```python
from opencoulomb.viz import (
    plot_volume_slices, plot_volume_cross_sections, plot_volume_3d,
    export_volume_gif, plot_catalog_on_volume,
)
```

### Beachball plots

```python
from opencoulomb.viz import plot_beachball, plot_beachballs_on_map
```

### GPS comparison

```python
from opencoulomb.viz import plot_gps_comparison, compute_misfit
```
