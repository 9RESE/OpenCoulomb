"""Performance benchmark tests for OpenCoulomb.

Level 6 of the 6-level validation suite.
Tests that computation meets performance targets.
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from opencoulomb.core.pipeline import compute_grid
from opencoulomb.io import parse_inp_string


def _make_benchmark_inp(
    n_faults: int = 10,
    grid_size: int = 100,
) -> str:
    """Build a benchmark .inp string with configurable faults and grid."""
    inc = 200.0 / grid_size

    # Generate n_faults evenly spaced source faults
    fault_lines = []
    for i in range(n_faults):
        y_pos = -50 + 100 * i / max(n_faults - 1, 1)
        fault_lines.append(
            f"    {i+1}     -20.0     {y_pos:8.1f}      20.0     {y_pos:8.1f}"
            f"  100       1.0       0.0    90.0     2.0    12.0  F{i+1}"
        )

    faults_block = "\n".join(fault_lines)

    return (
        "Benchmark model\n"
        "Performance benchmark for OpenCoulomb\n"
        f"#reg1=  0  #reg2=  0   #fixed=  {n_faults}  sym=  1\n"
        "PR1=       .250      PR2=       .250    DEPTH=        5.0\n"
        "E1=   0.800000E+06   E2=   0.800000E+06\n"
        "XSYM=       .000     YSYM=       .000\n"
        "FRIC=       .400\n"
        "S1DR=    19.0000     S1DP=      0.0000    S1IN=    100.000     S1GD=   .000000\n"
        "S3DR=   109.0000     S3DP=      0.0000    S3IN=     30.000     S3GD=   .000000\n"
        "S2DR=    19.0000     S2DP=    -90.0000    S2IN=      0.000     S2GD=   .000000\n"
        "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat    reverse"
        "   dip angle     top      bot\n"
        "xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx"
        " xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
        f"{faults_block}\n"
        "\n"
        "     Grid Parameters\n"
        "  1  ----------------------------  Start-x =   -100.00000\n"
        "  2  ----------------------------  Start-y =   -100.00000\n"
        f"  3  --------------------------   Finish-x =    100.00000\n"
        f"  4  --------------------------   Finish-y =    100.00000\n"
        f"  5  ------------------------  x-increment =     {inc:.6f}\n"
        f"  6  ------------------------  y-increment =     {inc:.6f}\n"
        "     Size Parameters\n"
        "  1  --------------------------  Plot size =     2.000000\n"
        "  2  --------------  Shade/Color increment =     1.000000\n"
        "  3  ------  Exaggeration for disp.& dist. =     10000.00\n"
    )


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance targets from the development plan."""

    def test_100x100_grid_10_faults_under_10s(self) -> None:
        """100x100 grid + 10 faults must compute in < 10 seconds."""
        inp_text = _make_benchmark_inp(n_faults=10, grid_size=100)
        model = parse_inp_string(inp_text)

        start = time.perf_counter()
        result = compute_grid(model)
        elapsed = time.perf_counter() - start

        assert result is not None
        assert not np.any(np.isnan(result.cfs))
        assert elapsed < 10.0, f"Computation took {elapsed:.2f}s (target: <10s)"

    def test_50x50_grid_5_faults_under_3s(self) -> None:
        """50x50 grid + 5 faults should be fast."""
        inp_text = _make_benchmark_inp(n_faults=5, grid_size=50)
        model = parse_inp_string(inp_text)

        start = time.perf_counter()
        result = compute_grid(model)
        elapsed = time.perf_counter() - start

        assert result is not None
        assert elapsed < 3.0, f"Computation took {elapsed:.2f}s (target: <3s)"

    def test_single_fault_linear_time(self) -> None:
        """Verify computation scales linearly with grid points."""
        small_inp = _make_benchmark_inp(n_faults=1, grid_size=20)
        large_inp = _make_benchmark_inp(n_faults=1, grid_size=40)
        small_model = parse_inp_string(small_inp)
        large_model = parse_inp_string(large_inp)

        start = time.perf_counter()
        compute_grid(small_model)
        small_time = time.perf_counter() - start

        start = time.perf_counter()
        compute_grid(large_model)
        large_time = time.perf_counter() - start

        # 4x more grid points should be < 8x slower (allowing overhead margin)
        ratio = large_time / max(small_time, 1e-6)
        assert ratio < 8.0, f"Scaling ratio {ratio:.1f}x (expected <8x for 4x grid)"
