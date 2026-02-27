"""Top-level model data structure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opencoulomb.types.fault import FaultElement
    from opencoulomb.types.grid import GridSpec
    from opencoulomb.types.material import MaterialProperties
    from opencoulomb.types.section import CrossSectionSpec
    from opencoulomb.types.stress import RegionalStress


@dataclass(slots=True)
class CoulombModel:
    """Complete input model for a Coulomb stress computation.

    This is the aggregate root: it contains everything needed to run
    a computation. It is produced by the .inp parser and consumed by
    the computation pipeline.

    Attributes
    ----------
    title : str
        Model title (from .inp file lines 1-2).
    material : MaterialProperties
        Elastic material properties.
    faults : list of FaultElement
        All fault elements (both source and receiver).
    grid : GridSpec
        Computation grid specification.
    n_fixed : int
        Number of source (fixed) fault elements. Elements 0..n_fixed-1
        are sources; n_fixed..end are receivers.
    regional_stress : RegionalStress or None
        Background regional stress field. None if not specified.
    cross_section : CrossSectionSpec or None
        Cross-section profile specification. None if not specified.
    symmetry : int
        Symmetry flag (1 = none). From .inp file.
    x_sym : float
        X symmetry axis (km).
    y_sym : float
        Y symmetry axis (km).
    """

    title: str
    material: MaterialProperties
    faults: list[FaultElement]
    grid: GridSpec
    n_fixed: int
    regional_stress: RegionalStress | None = None
    cross_section: CrossSectionSpec | None = None
    symmetry: int = 1
    x_sym: float = 0.0
    y_sym: float = 0.0

    @property
    def source_faults(self) -> list[FaultElement]:
        """Fault elements with non-zero slip (sources)."""
        return self.faults[: self.n_fixed]

    @property
    def receiver_faults(self) -> list[FaultElement]:
        """Fault elements with zero slip (receivers)."""
        return self.faults[self.n_fixed :]

    @property
    def n_sources(self) -> int:
        return self.n_fixed

    @property
    def n_receivers(self) -> int:
        return len(self.faults) - self.n_fixed
