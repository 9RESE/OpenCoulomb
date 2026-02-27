# Explanation: Coulomb Failure Stress

## What is Coulomb failure stress?

Coulomb failure stress (CFS, also written DCFS for "change in") is a scalar
quantity that measures how much closer a fault has been brought to failure
by a perturbation — such as a nearby earthquake, volcanic intrusion, or
fluid injection.

The concept rests on the **Coulomb failure criterion**, which states that
slip on a pre-existing fault occurs when:

```
tau = mu * sigma_n + C
```

where:
- `tau` — shear stress resolved on the fault plane
- `mu` — coefficient of friction (typically 0.4–0.8)
- `sigma_n` — effective normal stress (compression negative)
- `C` — cohesion (often neglected for pre-existing faults)

When an earthquake causes stress changes `delta_tau` and `delta_sigma_n`,
the change in Coulomb stress is:

```
DCFS = delta_tau + mu * delta_sigma_n
```

- **Positive DCFS** means the fault moved closer to failure (stress increased)
- **Negative DCFS** means the fault moved away from failure (stress shadow)

## Why does it matter?

Studies of earthquake sequences consistently show that aftershocks cluster
in regions of **positive** DCFS caused by the main shock. Regions of
**negative** DCFS have fewer aftershocks than background seismicity.

This makes CFS a useful tool for:

- **Aftershock forecasting** — identifying likely aftershock zones
- **Fault interaction studies** — assessing whether one earthquake promotes
  or inhibits slip on adjacent faults
- **Seismic hazard** — understanding how stress has evolved on major faults
  over a sequence of large earthquakes
- **Induced seismicity** — estimating whether fluid injection or reservoir
  changes bring faults closer to failure

## Sign conventions

OpenCoulomb uses the conventions of Coulomb 3.4 (USGS):

| Quantity | Positive | Negative |
|----------|----------|---------|
| Shear stress | In direction of receiver rake | Opposite |
| Normal stress | Extension (fault opens) | Compression |
| CFS | Promoted failure | Inhibited failure |
| Slip (rt.lat) | Right-lateral | Left-lateral |
| Slip (reverse) | Thrust/reverse | Normal |
| Depth | Downward | — |

Coordinates are Cartesian: X = east, Y = north, Z = up.

## Resolving stress onto a fault plane

The full 3D stress tensor `sigma_ij` must be projected onto a specific
fault plane defined by its strike, dip, and rake:

1. Compute the **normal vector** `n` to the fault plane from strike and dip
2. Compute the **rake direction vector** `d` from rake angle
3. Normal stress: `sigma_n = n · sigma · n`
4. Shear traction: `tau = d · sigma · n`
5. Apply Coulomb: `DCFS = tau + mu * sigma_n`

In OpenCoulomb this is done by `compute_cfs_on_receiver` in
`opencoulomb.core.coulomb`. The computation is fully vectorized over
all grid points using NumPy.

## Effect of friction coefficient

Friction `mu` controls the relative weighting of normal and shear changes:

- Low `mu` (0.2–0.3): normal stress changes dominate less; CFS pattern
  is more similar to the raw shear stress distribution
- High `mu` (0.6–0.8): fault unclamping (normal extension) contributes
  more strongly to CFS

The standard value `mu = 0.4` is used in most published studies and is
the Coulomb 3.4 default.

## Optimally oriented planes (OOPs)

When a regional stress field is specified in addition to the earthquake
stress, OpenCoulomb can compute the **optimally oriented failure plane**
at each grid point — the orientation that maximizes CFS given the combined
stress state. This is useful for areas where receiver fault orientation is
poorly constrained.

OOPs are computed only when `S1DR / S1DP / S1IN ...` are set in the `.inp`
file.

## Units

Stress is computed in **bar** throughout:

- 1 bar = 0.1 MPa = 10⁵ Pa
- Typical earthquake CFS changes: 0.01–10 bar
- Coulomb failure stress threshold (approximate): 0.1–1 bar

## Limitations

- The Okada model assumes a homogeneous, isotropic, elastic half-space.
  Real Earth has layered structure, viscosity, and fluid pore pressure.
- CFS is a static stress change; it does not include dynamic (seismic wave)
  stress or time-dependent viscoelastic relaxation.
- The result is sensitive to fault geometry, which is often poorly known
  for receiver faults.
- A fault with positive CFS is not guaranteed to produce an aftershock;
  CFS is a probabilistic stress-based metric, not a deterministic trigger.

## Further reading

- King, G.C.P., Stein, R.S., Lin, J. (1994). Static stress changes and the
  triggering of earthquakes. *Bulletin of the Seismological Society of America*,
  84(3), 935–953.
- Stein, R.S. (1999). The role of stress transfer in earthquake occurrence.
  *Nature*, 402, 605–609.
- Toda, S., Stein, R.S., Sevilgen, V., Lin, J. (2011). Coulomb 3.3
  Graphic-Rich Deformation and Stress-Change Software for Earthquake,
  Tectonic, and Volcano Research and Teaching. *USGS Open-File Report 2011-1060*.
