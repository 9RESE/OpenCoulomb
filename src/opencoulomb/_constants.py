"""Physical constants and default values for OpenCoulomb."""

import math

# --- Default material properties ---
DEFAULT_POISSON: float = 0.25
DEFAULT_YOUNG_BAR: float = 8.0e5       # 80 GPa in bar (1 bar = 0.1 MPa)
DEFAULT_FRICTION: float = 0.4
DEFAULT_DEPTH_KM: float = 10.0

# --- Unit conversion ---
KM_TO_M: float = 1000.0
M_TO_KM: float = 0.001
BAR_TO_PA: float = 1.0e5
PA_TO_BAR: float = 1.0e-5
BAR_TO_MPA: float = 0.1
MPA_TO_BAR: float = 10.0
# Strain unit factor: displacement gradients have units m/km = 0.001
# This corrects strains when computing stress in bar
STRAIN_UNIT_FACTOR: float = 0.001

# --- Numerical stability ---
SINGULARITY_THRESHOLD: float = 1.0e-12
DEPTH_EPSILON: float = 1.0e-6          # km, to avoid z=0 singularity

# --- Earth constants ---
EARTH_RADIUS_KM: float = 6371.0
DEG_TO_RAD: float = math.pi / 180.0
RAD_TO_DEG: float = 180.0 / math.pi

# --- Okada-specific ---
# Correction factor for free surface (image source)
FREE_SURFACE_FACTOR: float = 2.0

# --- Default computation parameters ---
DEFAULT_GRID_POINTS: int = 100     # Default number of grid points per axis
DEFAULT_GRID_DEPTH: float = 10.0   # Default computation depth (km)
