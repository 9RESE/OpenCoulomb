"""OpenCoulomb v0.2.0 Full Feature Demo.

Exercises every major feature of the package and produces
images + output files in the same directory as this script.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ── paths ──────────────────────────────────────────────────────────────
OUT = Path(__file__).parent
INP_SS = Path("tests/fixtures/inp_files/real/simplest_receiver.inp")   # strike-slip
INP_TH = Path("tests/fixtures/inp_files/real/M6.5.inp")               # oblique thrust
INP_SUB = Path("tests/fixtures/inp_files/real/test_case_subfaulted.inp")  # subfaulted

report_lines: list[str] = []

def log(msg: str) -> None:
    print(msg)
    report_lines.append(msg)


def save(fig: plt.Figure, name: str) -> Path:
    path = OUT / name
    fig.savefig(str(path), dpi=200, bbox_inches="tight")
    plt.close(fig)
    log(f"  -> saved {name}")
    return path


# ══════════════════════════════════════════════════════════════════════
log("=" * 70)
log("OpenCoulomb v0.2.0 — Full Feature Demo")
log("=" * 70)

from opencoulomb import __version__
log(f"Version: {__version__}")
log("")

# ── 1. Basic CFS computation ──────────────────────────────────────────
log("## 1. Basic CFS Computation (strike-slip)")
from opencoulomb.io import read_inp
from opencoulomb.core import compute_grid

model_ss = read_inp(str(INP_SS))
log(f"Model: {model_ss.title.splitlines()[0]}")
log(f"Sources: {model_ss.n_sources}, Grid: {model_ss.grid.n_x}x{model_ss.grid.n_y}")

t0 = time.perf_counter()
result_ss = compute_grid(model_ss)
dt = time.perf_counter() - t0
log(f"Compute time: {dt:.3f}s")
log(f"Peak CFS: {result_ss.cfs.max():.4f} bar")
log(f"Min  CFS: {result_ss.cfs.min():.4f} bar")
log("")

# ── 2. CFS map ────────────────────────────────────────────────────────
log("## 2. CFS Map")
from opencoulomb.viz import plot_cfs_map, plot_fault_traces, save_figure

fig, ax = plot_cfs_map(result_ss, model_ss)
ax.set_title("Strike-Slip CFS (bar)")
save(fig, "01_cfs_map_strikeslip.png")

# ── 3. Displacement field ─────────────────────────────────────────────
log("## 3. Displacement Field")
from opencoulomb.viz import plot_displacement

fig, ax = plot_displacement(result_ss, model_ss)
save(fig, "02_displacement_strikeslip.png")

# ── 4. Cross-section ──────────────────────────────────────────────────
log("## 4. Cross-Section")
from opencoulomb.core import compute_cross_section
from opencoulomb.viz import plot_cross_section

section_ss = compute_cross_section(model_ss)
log(f"Section shape: {section_ss.cfs.shape}")
fig, ax = plot_cross_section(section_ss)
save(fig, "03_cross_section_strikeslip.png")

# ── 5. Oblique thrust fault ───────────────────────────────────────────
log("")
log("## 5. Oblique Thrust Fault Model")
model_th = read_inp(str(INP_TH))
log(f"Model: {model_th.title.splitlines()[0]}")

result_th = compute_grid(model_th)
log(f"Peak CFS: {result_th.cfs.max():.4f} bar")

fig, ax = plot_cfs_map(result_th, model_th)
ax.set_title("Oblique Thrust CFS (bar)")
save(fig, "04_cfs_map_thrust.png")

section_th = compute_cross_section(model_th)
fig, ax = plot_cross_section(section_th)
save(fig, "05_cross_section_thrust.png")

# ── 6. Output writers ─────────────────────────────────────────────────
log("")
log("## 6. Output Writers")
from opencoulomb.io import write_csv, write_dcff_cou, write_coulomb_dat, write_summary

write_csv(result_ss, OUT / "strikeslip.csv")
write_dcff_cou(result_ss, model_ss, OUT / "strikeslip_dcff.cou")
write_coulomb_dat(result_ss, OUT / "strikeslip_cfs.dat")
write_summary(result_ss, model_ss, OUT / "strikeslip_summary.txt")
log("  -> wrote strikeslip.csv, .cou, .dat, _summary.txt")

# ── 7. Scaling Relations ──────────────────────────────────────────────
log("")
log("## 7. Scaling Relations")
from opencoulomb.core import wells_coppersmith_1994, blaser_2010, magnitude_to_fault

magnitudes = [5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0]
log(f"{'Mag':>4s} | {'WC94 L(km)':>10s} | {'WC94 W(km)':>10s} | {'WC94 D(m)':>10s} | {'Blaser L':>10s} | {'Blaser W':>10s}")
log("-" * 70)
for m in magnitudes:
    wc = wells_coppersmith_1994(m)
    bl = blaser_2010(m)
    log(f"{m:4.1f} | {wc.length_km:10.2f} | {wc.width_km:10.2f} | {wc.displacement_m:10.3f} | {bl.length_km:10.2f} | {bl.width_km:10.2f}")

# Plot scaling curves
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
mags = np.arange(4.5, 8.5, 0.1)
for label, func, ls in [("Wells & Coppersmith 1994", wells_coppersmith_1994, "-"),
                         ("Blaser et al. 2010", blaser_2010, "--")]:
    lengths = [func(m).length_km for m in mags]
    widths = [func(m).width_km for m in mags]
    disps = [func(m).displacement_m for m in mags]
    axes[0].plot(mags, lengths, ls, label=label)
    axes[1].plot(mags, widths, ls, label=label)
    axes[2].plot(mags, disps, ls, label=label)
axes[0].set(xlabel="Magnitude", ylabel="Length (km)", title="Rupture Length", yscale="log")
axes[1].set(xlabel="Magnitude", ylabel="Width (km)", title="Rupture Width", yscale="log")
axes[2].set(xlabel="Magnitude", ylabel="Displacement (m)", title="Average Displacement", yscale="log")
for ax in axes:
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
fig.suptitle("Earthquake Scaling Relations", fontweight="bold")
fig.tight_layout()
save(fig, "06_scaling_relations.png")

# Create a fault from magnitude
fault_m7 = magnitude_to_fault(7.0, center_x=0, center_y=0, strike=0, dip=90, rake=0, top_depth=0)
log(f"M7.0 fault: length={fault_m7.x_fin - fault_m7.x_start:.1f} km, "
    f"depth={fault_m7.top_depth:.1f}-{fault_m7.bottom_depth:.1f} km")
log("")

# ── 8. Strain Output ──────────────────────────────────────────────────
log("## 8. Strain Computation")
result_strain = compute_grid(model_ss, compute_strain=True)
strain = result_strain.strain
log(f"Strain computed: {strain is not None}")
if strain is not None:
    ny, nx = result_strain.grid_shape
    log(f"Volumetric strain range: [{strain.volumetric.min():.2e}, {strain.volumetric.max():.2e}]")

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    components = [
        ("exx", strain.exx), ("eyy", strain.eyy), ("ezz", strain.ezz),
        ("eyz", strain.eyz), ("exz", strain.exz), ("exy", strain.exy),
    ]
    x2d = result_strain.stress.x.reshape(ny, nx)
    y2d = result_strain.stress.y.reshape(ny, nx)
    for ax, (name, data) in zip(axes.ravel(), components):
        d2d = data.reshape(ny, nx)
        vmax = np.percentile(np.abs(d2d), 98)
        if vmax == 0:
            vmax = 1e-10
        im = ax.contourf(x2d, y2d, d2d, levels=21, cmap="RdBu_r",
                         vmin=-vmax, vmax=vmax)
        ax.set_title(f"Strain: {name}")
        ax.set_aspect("equal")
        fig.colorbar(im, ax=ax, shrink=0.8)
    fig.suptitle("Full Strain Tensor", fontweight="bold")
    fig.tight_layout()
    save(fig, "07_strain_tensor.png")

    # Volumetric strain (dilatation)
    fig, ax = plt.subplots(figsize=(8, 6))
    vol = strain.volumetric.reshape(ny, nx)
    vmax = np.percentile(np.abs(vol), 98)
    if vmax == 0:
        vmax = 1e-10
    im = ax.contourf(x2d, y2d, vol, levels=21, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_title("Volumetric Strain (Dilatation)")
    ax.set_xlabel("East (km)")
    ax.set_ylabel("North (km)")
    ax.set_aspect("equal")
    fig.colorbar(im, ax=ax, label="Dilatation")
    save(fig, "08_volumetric_strain.png")
log("")

# ── 9. Slip Tapering ──────────────────────────────────────────────────
log("## 9. Slip Tapering")
from opencoulomb.core import TaperSpec, TaperProfile, taper_function

# Plot taper profiles
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
xi = np.linspace(0, 1, 200)
for ax, profile in zip(axes, [TaperProfile.COSINE, TaperProfile.LINEAR, TaperProfile.ELLIPTICAL]):
    for tw in [0.1, 0.2, 0.3, 0.5]:
        weights = [taper_function(x, profile, tw) for x in xi]
        ax.plot(xi, weights, label=f"tw={tw}")
    ax.set_title(f"{profile.value.title()} Taper")
    ax.set_xlabel("Normalized position")
    ax.set_ylabel("Weight")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
fig.suptitle("Slip Taper Profiles", fontweight="bold")
fig.tight_layout()
save(fig, "09_taper_profiles.png")

# Compute with tapering vs no tapering
taper = TaperSpec(profile=TaperProfile.COSINE, n_along_strike=5, n_down_dip=3, taper_width_fraction=0.2)
result_tapered = compute_grid(model_ss, taper=taper)
log(f"Tapered peak CFS: {result_tapered.cfs.max():.4f} bar (vs {result_ss.cfs.max():.4f} untapered)")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
ny, nx = result_ss.grid_shape
x2d = result_ss.stress.x.reshape(ny, nx)
y2d = result_ss.stress.y.reshape(ny, nx)
vmax = max(np.percentile(np.abs(result_ss.cfs), 98), np.percentile(np.abs(result_tapered.cfs), 98))
for ax, res, title in [(axes[0], result_ss, "No Taper"), (axes[1], result_tapered, "Cosine Taper (5x3)")]:
    cfs2d = res.cfs.reshape(ny, nx)
    im = ax.contourf(x2d, y2d, cfs2d, levels=21, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.set_xlabel("East (km)")
    ax.set_ylabel("North (km)")
    fig.colorbar(im, ax=ax, label="CFS (bar)")
fig.suptitle("Effect of Slip Tapering on CFS", fontweight="bold")
fig.tight_layout()
save(fig, "10_taper_comparison.png")
log("")

# ── 10. 3D Volume Computation ─────────────────────────────────────────
log("## 10. 3D Volume Computation")
from opencoulomb.core import compute_volume
from opencoulomb.types import VolumeGridSpec

vol_spec = VolumeGridSpec(
    start_x=model_ss.grid.start_x,
    start_y=model_ss.grid.start_y,
    finish_x=model_ss.grid.finish_x,
    finish_y=model_ss.grid.finish_y,
    x_inc=model_ss.grid.x_inc,
    y_inc=model_ss.grid.y_inc,
    depth_min=2.0,
    depth_max=20.0,
    depth_inc=2.0,
)
log(f"Volume: {vol_spec.n_x}x{vol_spec.n_y}x{vol_spec.n_z} = {vol_spec.n_points} points")
log(f"Depths: {list(vol_spec.depths)} km")

t0 = time.perf_counter()
volume = compute_volume(model_ss, vol_spec)
dt = time.perf_counter() - t0
log(f"Volume compute time: {dt:.1f}s")

cfs_3d = volume.cfs_volume()
log(f"3D CFS shape: {cfs_3d.shape}")
log(f"3D CFS range: [{cfs_3d.min():.4f}, {cfs_3d.max():.4f}] bar")
log("")

# ── 11. Volume Visualization: Slices ──────────────────────────────────
log("## 11. Volume Depth Slices")
from opencoulomb.viz import plot_volume_slices

fig, axes = plot_volume_slices(volume, model_ss)
fig.suptitle("CFS at Multiple Depths", fontweight="bold", y=1.02)
save(fig, "11_volume_slices.png")

# ── 12. Volume Cross-Sections ─────────────────────────────────────────
log("## 12. Volume Cross-Sections")
from opencoulomb.viz import plot_volume_cross_sections

fig, axes = plot_volume_cross_sections(volume, model_ss)
fig.suptitle("Vertical E-W Cross-Sections through Volume", fontweight="bold", y=1.02)
save(fig, "12_volume_cross_sections.png")

# ── 13. Volume 3D Scatter ─────────────────────────────────────────────
log("## 13. 3D Volume Scatter Plot")
try:
    from opencoulomb.viz import plot_volume_3d
    fig, ax = plot_volume_3d(volume, model_ss, threshold=0.005)
    save(fig, "13_volume_3d.png")
except (ValueError, ImportError) as exc:
    log(f"  -> SKIPPED (matplotlib 3D projection unavailable: {exc!r})")

# ── 14. Volume GIF ────────────────────────────────────────────────────
log("## 14. Animated Volume GIF")
from opencoulomb.viz import export_volume_gif

gif_path = export_volume_gif(volume, model_ss, OUT / "14_volume_depth_animation.gif", fps=3)
log(f"  -> saved {gif_path.name} ({gif_path.stat().st_size / 1024:.0f} KB)")
log("")

# ── 15. Volume Writers ────────────────────────────────────────────────
log("## 15. Volume Output Files")
from opencoulomb.io import write_volume_csv, write_volume_slices

write_volume_csv(volume, OUT / "volume_3d.csv")
slice_dir = OUT / "volume_slices"
slice_dir.mkdir(exist_ok=True)
write_volume_slices(volume, slice_dir)
n_slices = len(list(slice_dir.glob("*.dat")))
log(f"  -> wrote volume_3d.csv ({(OUT / 'volume_3d.csv').stat().st_size / 1024:.0f} KB)")
log(f"  -> wrote {n_slices} depth slice .dat files to volume_slices/")
log("")

# ── 16. Earthquake Catalog ────────────────────────────────────────────
log("## 16. Synthetic Earthquake Catalog")
from opencoulomb.types.catalog import CatalogEvent, EarthquakeCatalog
from opencoulomb.io import write_catalog_csv, read_catalog_csv

# Create a synthetic catalog (simulating aftershock pattern)
rng = np.random.default_rng(42)
n_events = 50
events = []
for i in range(n_events):
    events.append(CatalogEvent(
        latitude=rng.uniform(-15, 15),
        longitude=rng.uniform(-15, 15),
        depth_km=rng.uniform(2, 25),
        magnitude=rng.uniform(2.0, 5.5),
        time=f"2024-01-{rng.integers(1, 31):02d}T{rng.integers(0, 24):02d}:00:00",
        event_id=f"ev{i:04d}",
        magnitude_type="ML",
    ))
catalog = EarthquakeCatalog(events=events, source="synthetic")
log(f"Created {len(catalog)} synthetic events")

# Write and read back
write_catalog_csv(catalog, OUT / "synthetic_catalog.csv")
catalog_back = read_catalog_csv(OUT / "synthetic_catalog.csv")
log(f"CSV round-trip: {len(catalog_back)} events recovered")

# Filter
big = catalog.filter_by_magnitude(min_mag=4.0)
shallow = catalog.filter_by_depth(max_depth=10.0)
log(f"Filtered: {len(big)} events M>=4.0, {len(shallow)} events depth<=10km")
log("")

# ── 17. Catalog on Volume ─────────────────────────────────────────────
log("## 17. Catalog Overlay on Volume Slice")
from opencoulomb.viz import plot_catalog_on_volume

fig, ax = plot_catalog_on_volume(volume, model_ss, catalog, depth_index=4)
ax.set_title(f"CFS at {volume.depths[4]:.0f} km + Catalog Events")
save(fig, "15_catalog_on_volume.png")

# ── 18. Beachball Focal Mechanisms ────────────────────────────────────
log("## 18. Beachball Focal Mechanisms")
from opencoulomb.viz import plot_beachball

fig, axes = plt.subplots(1, 4, figsize=(16, 4))
mechanisms = [
    (0, 90, 0, "Pure Strike-Slip"),
    (0, 45, 90, "Pure Thrust"),
    (0, 45, -90, "Pure Normal"),
    (45, 60, 30, "Oblique"),
]
for ax, (s, d, r, title) in zip(axes, mechanisms):
    plot_beachball(s, d, r, (0, 0), ax, size=40, facecolor="red")
    ax.set_title(f"{title}\nS={s} D={d} R={r}")
    ax.set_xlim(-50, 50)
    ax.set_ylim(-50, 50)
    ax.set_aspect("equal")
fig.suptitle("Focal Mechanism Beachballs", fontweight="bold")
fig.tight_layout()
save(fig, "16_beachballs.png")

# Beachballs on CFS map
log("## 19. Beachballs on CFS Map")
from opencoulomb.viz import plot_beachballs_on_map

fig, ax = plot_beachballs_on_map(result_ss, model_ss)
save(fig, "17_beachballs_on_map.png")

fig, ax = plot_beachballs_on_map(result_ss, model_ss, catalog=catalog)
save(fig, "18_beachballs_with_catalog.png")
log("")

# ── 20. GPS Comparison ────────────────────────────────────────────────
log("## 20. GPS Displacement Comparison")
from opencoulomb.types.gps import GPSStation, GPSDataset
from opencoulomb.viz.gps import plot_gps_comparison, compute_misfit

# Create synthetic GPS stations with "observed" displacements
# (true model displacement + noise)
ux_2d, uy_2d, uz_2d = result_ss.displacement_grid()
ny, nx = result_ss.grid_shape
x1d = result_ss.stress.x.reshape(ny, nx)[0, :]
y1d = result_ss.stress.y.reshape(ny, nx)[:, 0]

stations = []
station_locs = [
    ("STA01", -20, -20), ("STA02", 0, -15), ("STA03", 20, -20),
    ("STA04", -20, 0),   ("STA05", 5, 5),   ("STA06", 20, 0),
    ("STA07", -20, 20),  ("STA08", 0, 15),  ("STA09", 20, 20),
    ("STA10", -10, -5),  ("STA11", 10, 5),  ("STA12", 0, -25),
]

from scipy.interpolate import RegularGridInterpolator
interp_ux = RegularGridInterpolator((y1d, x1d), ux_2d, bounds_error=False, fill_value=0.0)
interp_uy = RegularGridInterpolator((y1d, x1d), uy_2d, bounds_error=False, fill_value=0.0)
interp_uz = RegularGridInterpolator((y1d, x1d), uz_2d, bounds_error=False, fill_value=0.0)

for name, sx, sy in station_locs:
    pt = np.array([[sy, sx]])
    true_ux = float(interp_ux(pt))
    true_uy = float(interp_uy(pt))
    true_uz = float(interp_uz(pt))
    # Add realistic noise (10% of signal + small baseline)
    noise_scale = max(0.001, 0.1 * np.sqrt(true_ux**2 + true_uy**2))
    obs_ux = true_ux + rng.normal(0, noise_scale)
    obs_uy = true_uy + rng.normal(0, noise_scale)
    obs_uz = true_uz + rng.normal(0, noise_scale * 0.5)
    stations.append(GPSStation(
        name=name, x=float(sx), y=float(sy),
        ux=obs_ux, uy=obs_uy, uz=obs_uz,
        sigma_ux=noise_scale, sigma_uy=noise_scale, sigma_uz=noise_scale * 0.5,
    ))

gps = GPSDataset(stations=stations, reference_frame="local")
log(f"Created {len(gps.stations)} synthetic GPS stations")

# Plot horizontal comparison
fig, ax = plot_gps_comparison(result_ss, model_ss, gps, component="horizontal", show_residuals=True)
save(fig, "19_gps_horizontal.png")

# Plot vertical comparison
fig, ax = plot_gps_comparison(result_ss, model_ss, gps, component="vertical")
save(fig, "20_gps_vertical.png")

# Compute misfit
misfit = compute_misfit(result_ss, model_ss, gps)
log(f"GPS Misfit:")
log(f"  RMS horizontal: {misfit['rms_horizontal']:.6f} m")
log(f"  RMS vertical:   {misfit['rms_vertical']:.6f} m")
log(f"  RMS 3D:         {misfit['rms_3d']:.6f} m")
log(f"  Reduction of variance: {misfit['reduction_of_variance']:.4f}")

# Write GPS data
gps_csv = OUT / "synthetic_gps.csv"
with open(gps_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["station_name", "x", "y", "ux", "uy", "uz",
                                       "sigma_ux", "sigma_uy", "sigma_uz"])
    w.writeheader()
    for s in gps.stations:
        w.writerow({"station_name": s.name, "x": s.x, "y": s.y,
                     "ux": s.ux, "uy": s.uy, "uz": s.uz,
                     "sigma_ux": s.sigma_ux, "sigma_uy": s.sigma_uy, "sigma_uz": s.sigma_uz})
log(f"  -> saved synthetic_gps.csv")
log("")

# ── 21. Subfaulted model ──────────────────────────────────────────────
log("## 21. Subfaulted Source (101 patches)")
model_sub = read_inp(str(INP_SUB))
log(f"Sources: {model_sub.n_sources}")
t0 = time.perf_counter()
result_sub = compute_grid(model_sub)
dt = time.perf_counter() - t0
log(f"Compute time: {dt:.3f}s")
log(f"Peak CFS: {result_sub.cfs.max():.4f} bar")

fig, ax = plot_cfs_map(result_sub, model_sub)
ax.set_title("Subfaulted Source CFS (101 patches)")
save(fig, "21_subfaulted_cfs.png")
log("")

# ── 22. Multiple fields on volume ─────────────────────────────────────
log("## 22. Volume Fields: CFS, Shear, Normal")
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
mid_depth = volume.volume_shape[0] // 2
ny_v, nx_v = volume.volume_shape[1], volume.volume_shape[2]
slice_r = volume.slice_at_depth(mid_depth)
x2d_v = slice_r.stress.x.reshape(ny_v, nx_v)
y2d_v = slice_r.stress.y.reshape(ny_v, nx_v)

for ax, field_name, data_flat in [
    (axes[0], "CFS", volume.cfs),
    (axes[1], "Shear", volume.shear),
    (axes[2], "Normal", volume.normal),
]:
    data_3d = data_flat.reshape(volume.volume_shape)
    d2d = data_3d[mid_depth]
    vmax = np.percentile(np.abs(d2d), 98)
    if vmax == 0:
        vmax = 1e-6
    im = ax.contourf(x2d_v, y2d_v, d2d, levels=21, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_title(f"{field_name} at {volume.depths[mid_depth]:.0f} km")
    ax.set_aspect("equal")
    ax.set_xlabel("East (km)")
    fig.colorbar(im, ax=ax, label=f"{field_name} (bar)")
axes[0].set_ylabel("North (km)")
fig.suptitle(f"Stress Fields at {volume.depths[mid_depth]:.0f} km Depth", fontweight="bold")
fig.tight_layout()
save(fig, "22_volume_fields.png")
log("")

# ── 23. Volume with tapering ──────────────────────────────────────────
log("## 23. Volume + Tapering")
volume_tapered = compute_volume(model_ss, vol_spec, taper=taper)
log(f"Tapered volume peak CFS: {volume_tapered.cfs.max():.4f} bar")
fig, axes = plot_volume_slices(volume_tapered, model_ss, depth_indices=[0, 4, 8])
fig.suptitle("Tapered Volume CFS Slices", fontweight="bold", y=1.02)
save(fig, "23_volume_tapered_slices.png")
log("")

# ══════════════════════════════════════════════════════════════════════
# Write report
log("")
log("=" * 70)
log("SUMMARY")
log("=" * 70)

images = sorted(OUT.glob("*.png")) + sorted(OUT.glob("*.gif"))
log(f"Total images generated: {len(images)}")
for img in images:
    log(f"  {img.name} ({img.stat().st_size / 1024:.0f} KB)")

data_files = sorted(OUT.glob("*.csv")) + sorted(OUT.glob("*.cou")) + sorted(OUT.glob("*.dat")) + sorted(OUT.glob("*.txt"))
log(f"\nTotal data files: {len(data_files)}")
for f in data_files:
    log(f"  {f.name} ({f.stat().st_size / 1024:.0f} KB)")

report_path = OUT / "REPORT.md"
with open(report_path, "w") as f:
    f.write("# OpenCoulomb v0.2.0 — Full Feature Test Report\n\n")
    f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    for line in report_lines:
        if line.startswith("## "):
            f.write(f"\n{line}\n\n")
        elif line.startswith("=="):
            f.write(f"\n---\n\n")
        elif line.startswith("  -> saved "):
            fname = line.split("saved ")[1]
            if fname.endswith(".png") or fname.endswith(".gif"):
                f.write(f"![{fname}]({fname})\n\n")
            else:
                f.write(f"{line}\n")
        else:
            f.write(f"{line}\n")

log(f"\nReport: {report_path.name}")
log("Done!")
