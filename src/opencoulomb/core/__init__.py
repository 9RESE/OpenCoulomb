"""Core computation engine."""

from opencoulomb.core.coordinates import (
    compute_fault_geometry,
    direction_cosines,
    fault_to_geo_displacement,
    geo_to_fault,
    rotation_matrix,
    strike_dip_to_normal,
)
from opencoulomb.core.coulomb import compute_cfs, compute_cfs_on_receiver, resolve_stress_on_fault
from opencoulomb.core.okada import dc3d, dc3d0
from opencoulomb.core.oops import (
    compute_regional_stress_tensor,
    find_optimal_planes,
    mohr_coulomb_angle,
)
from opencoulomb.core.pipeline import compute_cross_section, compute_element_cfs, compute_grid
from opencoulomb.core.stress import gradients_to_stress, rotate_stress_tensor

__all__ = [
    "compute_cfs",
    "compute_cfs_on_receiver",
    "compute_cross_section",
    "compute_element_cfs",
    "compute_fault_geometry",
    "compute_grid",
    "compute_regional_stress_tensor",
    "dc3d",
    "dc3d0",
    "direction_cosines",
    "fault_to_geo_displacement",
    "find_optimal_planes",
    "geo_to_fault",
    "gradients_to_stress",
    "mohr_coulomb_angle",
    "resolve_stress_on_fault",
    "rotate_stress_tensor",
    "rotation_matrix",
    "strike_dip_to_normal",
]
