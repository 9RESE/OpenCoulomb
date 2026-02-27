"""Shared pytest fixtures for the OpenCoulomb test suite."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # non-interactive backend — must be set before pyplot import

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
INP_FILES_DIR = FIXTURES_DIR / "inp_files"
REAL_INP_FILES_DIR = INP_FILES_DIR / "real"
COULOMB34_INP_DIR = INP_FILES_DIR / "coulomb34"
USGS_FF_INP_DIR = INP_FILES_DIR / "usgs_finite_fault"
REFERENCE_OUTPUTS_DIR = FIXTURES_DIR / "reference_outputs"
OKADA_REFERENCE_DIR = FIXTURES_DIR / "okada_reference"


@pytest.fixture(autouse=True)
def close_matplotlib_figures() -> None:
    """Close all open matplotlib figures after each test to prevent resource leaks."""
    yield
    import matplotlib.pyplot as plt
    plt.close("all")


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Return the absolute path to the fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def inp_files_dir() -> Path:
    """Return the absolute path to the sample .inp files directory."""
    return INP_FILES_DIR


@pytest.fixture(scope="session")
def reference_outputs_dir() -> Path:
    """Return the absolute path to reference output files directory."""
    return REFERENCE_OUTPUTS_DIR


@pytest.fixture(scope="session")
def real_inp_files_dir() -> Path:
    """Return the absolute path to the real Coulomb .inp files directory."""
    return REAL_INP_FILES_DIR


@pytest.fixture(scope="session")
def coulomb34_inp_dir() -> Path:
    """Return the absolute path to Coulomb 3.4 distribution example files."""
    return COULOMB34_INP_DIR


@pytest.fixture(scope="session")
def usgs_ff_inp_dir() -> Path:
    """Return the absolute path to USGS finite-fault .inp files."""
    return USGS_FF_INP_DIR


@pytest.fixture(scope="session")
def okada_reference_dir() -> Path:
    """Return the absolute path to Okada (1992) reference values directory."""
    return OKADA_REFERENCE_DIR
