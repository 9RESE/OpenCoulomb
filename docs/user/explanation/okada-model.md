# Explanation: The Okada Dislocation Model

## Overview

OpenCoulomb computes displacements and stresses using the **Okada (1985, 1992)**
analytical solutions for dislocation in an elastic half-space. These are
exact closed-form solutions — no numerical discretization of the Earth is
required.

## What the model computes

Given a rectangular fault patch defined by:
- Fault center depth
- Length and width
- Dip angle
- Strike-slip, dip-slip, and tensile dislocation

The Okada solution returns the **displacement and its spatial gradients** at
any observation point in the half-space:

```
ux, uy, uz          — displacement (3 components)
uxx, uxy, uxz       — gradient of ux
uyx, uyy, uyz       — gradient of uy
uzx, uzy, uzz       — gradient of uz
```

From the displacement gradients, stresses are computed via Hooke's law (linear
elasticity).

## Coordinate system

The Okada functions use a **fault-local** coordinate system:
- x-axis: along fault strike (positive in strike direction)
- y-axis: perpendicular to fault strike, horizontal
- z-axis: upward (positive)
- Origin: at the surface projection of the fault center

OpenCoulomb handles the transformation between geographic (East-North-Up)
and fault-local coordinates internally.

## Elastic half-space assumptions

The Okada model makes these assumptions about the Earth:

| Assumption | Reality |
|-----------|---------|
| Homogeneous | Earth has layers |
| Isotropic | Some anisotropy exists |
| Linear elastic | Inelastic behavior near faults |
| Poisson solid | Valid for crustal rock |
| Flat free surface | Valid for regional scale |

For regional-scale CFS calculations (tens to hundreds of km), these
approximations introduce errors of roughly 10–20%, smaller than uncertainties
in fault geometry and friction.

## The two Okada functions

OpenCoulomb exposes both:

### `dc3d` — finite rectangular fault

Used for standard fault dislocation sources (Kode 100, 200, 300):

```python
from opencoulomb.core import dc3d

result = dc3d(
    alpha,          # elastic parameter = (lambda + mu) / (lambda + 2*mu)
    x, y, z,        # observation point coordinates
    depth,          # fault top depth (km, positive)
    dip,            # dip angle (degrees from horizontal)
    al1, al2,       # along-strike half-lengths (km)
    aw1, aw2,       # along-dip half-widths (km)
    disl1,          # strike-slip dislocation (m)
    disl2,          # dip-slip dislocation (m)
    disl3,          # tensile dislocation (m)
)
# Returns 12-tuple: (ux, uy, uz, uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz)
```

### `dc3d0` — point source

Used for point sources and pressurized cavities (Kode 400, 500):

```python
from opencoulomb.core import dc3d0

result = dc3d0(
    alpha,
    x, y, z,
    depth,
    dip,
    pot1,   # strike-slip potency
    pot2,   # dip-slip potency
    pot3,   # tensile potency
    pot4,   # inflation potency
)
```

## From gradients to stress

Displacement gradients are converted to stress via the constitutive law for a
linear elastic solid. In index notation:

```
epsilon_ij = 0.5 * (u_i,j + u_j,i)    [strain tensor]
sigma_ij = lambda * delta_ij * epsilon_kk + 2*mu * epsilon_ij
```

where `lambda` and `mu` are the Lamé parameters, related to the user-supplied
Young's modulus `E` and Poisson's ratio `nu`:

```
lambda = E * nu / ((1 + nu) * (1 - 2*nu))
mu     = E / (2 * (1 + nu))
```

In OpenCoulomb this is `gradients_to_stress` in `opencoulomb.core.stress`.

## Superposition

For models with multiple source faults, OpenCoulomb uses **linear superposition**:
each fault's displacement and stress contribution is computed independently,
then summed. This is valid under linear elasticity.

```python
# Conceptually:
total_ux = fault1_ux + fault2_ux + fault3_ux + ...
total_sxx = fault1_sxx + fault2_sxx + fault3_sxx + ...
```

## Slip sign conventions

The Okada convention for dislocation sign differs from the Coulomb 3.4
convention. OpenCoulomb handles the conversion internally:

| Coulomb .inp | Okada `disl` |
|-------------|-------------|
| `rt.lat > 0` (right-lateral) | `disl1 < 0` (Okada is left-lateral positive) |
| `reverse > 0` (thrust) | `disl2 > 0` |
| Tensile opening | `disl3 > 0` |

## Numerical accuracy

The Okada solution is analytical and exact for the elastic half-space model.
The main source of numerical error is floating-point arithmetic near:

- The fault surface itself (singularity at zero distance)
- The free surface directly above the fault

OpenCoulomb excludes near-singularity points automatically (they appear as
`NaN` in the output grid near source fault traces).

Validation against Okada (1992) Table 2 reference values achieves errors
below `1e-10` for displacements.

## References

- Okada, Y. (1985). Surface deformation due to shear and tensile faults in a
  half-space. *Bulletin of the Seismological Society of America*, 75(4), 1135–1154.
- Okada, Y. (1992). Internal deformation due to shear and tensile faults in a
  half-space. *Bulletin of the Seismological Society of America*, 82(2), 1018–1040.
