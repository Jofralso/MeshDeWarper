"""Interpolation accuracy tests using synthetic distortion fields.

Each test creates a known analytical distortion, samples a coarse mesh,
interpolates at known points, and compares against the ground truth.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest

from mesh_de_warper.core.mesh import Mesh
from mesh_de_warper.core.point import Point
from mesh_de_warper.interpolation.base import InterpolationAlgorithm
from mesh_de_warper.interpolation.bicubic import BicubicInterpolation
from mesh_de_warper.interpolation.bilinear import BilinearInterpolation
from mesh_de_warper.interpolation.rbf import RBFInterpolation
from mesh_de_warper.interpolation.tps import ThinPlateSplineInterpolation

np.random.seed(42)

# ── Synthetic distortion functions ──────────────────────────────────


def uniform_shift(x: float, y: float) -> tuple[float, float]:
    """Constant offset — perfect reconstruction expected."""
    return 5.0, -3.0


def linear_gradient(x: float, y: float) -> tuple[float, float]:
    """Linearly varying offset."""
    return 0.1 * x + 0.05 * y, -0.03 * x + 0.08 * y


def radial_distortion(
    x: float, y: float, cx: float = 100.0, cy: float = 100.0, k: float = 1e-5
) -> tuple[float, float]:
    """Radial pincushion/barrel distortion."""
    dx = x - cx
    dy = y - cy
    r2 = dx * dx + dy * dy
    factor = k * r2
    return dx * factor, dy * factor


def _radial100(x: float, y: float) -> tuple[float, float]:
    """Radial distortion centred at (100, 100) with k=1e-5."""
    return radial_distortion(x, y, 100.0, 100.0, 1e-5)


def sinusoidal_warp(x: float, y: float) -> tuple[float, float]:
    """Sinusoidal periodic distortion."""
    return 2.0 * math.sin(0.05 * y), 2.0 * math.cos(0.05 * x)


# ── Helpers ─────────────────────────────────────────────────────────


def build_mesh_from_func(
    rows: int,
    cols: int,
    width: float,
    height: float,
    func,
) -> Mesh:
    """Build a Mesh whose offset at each node is *func(x, y)."""
    spacing_x = width / (cols - 1) if cols > 1 else width
    spacing_y = height / (rows - 1) if rows > 1 else height
    spacing = min(spacing_x, spacing_y)
    m = Mesh(width, height, spacing)
    for r in range(m.rows):
        for c in range(m.cols):
            x = m[r, c].x
            y = m[r, c].y
            ox, oy = func(x, y)
            m[r, c] = Point(x, y, ox, oy)
    return m


def rmse(interp: InterpolationAlgorithm, mesh: Mesh, func, n_samples: int = 100) -> float:
    """Root-mean-square error between interpolated and ground-truth offset."""
    errors = []
    for _ in range(n_samples):
        x = np.random.uniform(0, mesh.width)
        y = np.random.uniform(0, mesh.height)
        ix, iy = interp.interpolate(mesh, x, y)
        tx, ty = func(x, y)
        errors.append(math.hypot(ix - tx, iy - ty))
    return math.sqrt(sum(e * e for e in errors) / len(errors)) if errors else 0.0


# ── Test configurations ─────────────────────────────────────────────

INTERPOLATORS = [
    pytest.param(BilinearInterpolation(), id="bilinear"),
    pytest.param(BicubicInterpolation(), id="bicubic"),
    pytest.param(ThinPlateSplineInterpolation(), id="tps"),
    pytest.param(RBFInterpolation(kernel="thin_plate_spline"), id="rbf-tps"),
    pytest.param(RBFInterpolation(kernel="gaussian", epsilon=0.03), id="rbf-gaussian"),
    pytest.param(RBFInterpolation(kernel="multiquadric", epsilon=0.03), id="rbf-mq"),
    pytest.param(RBFInterpolation(kernel="inverse_multiquadric", epsilon=0.03), id="rbf-imq"),
]

COARSE_MESH = (5, 5, 200.0, 200.0)  # rows, cols, width, height
FINE_MESH = (9, 9, 200.0, 200.0)

EXPECTED_ACCURACY = {
    "uniform": {
        "bilinear": 0.01,
        "bicubic": 0.01,
        "tps": 0.01,
        "rbf-tps": 0.01,
        "rbf-gaussian": 0.01,
        "rbf-mq": 0.01,
        "rbf-imq": 0.01,
    },
    "linear": {
        "bilinear": 0.5,
        "bicubic": 0.5,
        "tps": 0.5,
        "rbf-tps": 0.5,
        "rbf-gaussian": 16.0,
        "rbf-mq": 12.0,
        "rbf-imq": 12.0,
    },
    "radial_coarse": {
        "bilinear": 1.6,
        "bicubic": 1.6,
        "tps": 0.8,
        "rbf-tps": 0.8,
        "rbf-gaussian": 2.5,
        "rbf-mq": 2.0,
        "rbf-imq": 2.5,
    },
    "radial_fine": {
        "bilinear": 0.5,
        "bicubic": 0.5,
        "tps": 0.15,
        "rbf-tps": 0.15,
        "rbf-gaussian": 1.2,
        "rbf-mq": 0.5,
        "rbf-imq": 0.8,
    },
}


def _interp_key(interp: InterpolationAlgorithm) -> str:
    if isinstance(interp, BilinearInterpolation):
        return "bilinear"
    if isinstance(interp, BicubicInterpolation):
        return "bicubic"
    if isinstance(interp, ThinPlateSplineInterpolation):
        return "tps"
    if isinstance(interp, RBFInterpolation):
        if interp._kernel == "thin_plate_spline":
            return "rbf-tps"
        if interp._kernel == "gaussian":
            return "rbf-gaussian"
        if interp._kernel == "multiquadric":
            return "rbf-mq"
        if interp._kernel == "inverse_multiquadric":
            return "rbf-imq"
    return "unknown"


# ── Tests ───────────────────────────────────────────────────────────


class TestInterpolationAccuracy:
    @pytest.mark.parametrize("interp", INTERPOLATORS)
    def test_uniform_shift(self, interp: InterpolationAlgorithm) -> None:
        mesh = build_mesh_from_func(*COARSE_MESH, uniform_shift)
        err = rmse(interp, mesh, uniform_shift, n_samples=200)
        key = _interp_key(interp)
        assert err < EXPECTED_ACCURACY["uniform"][key], f"{key} RMSE {err:.4f}"

    @pytest.mark.parametrize("interp", INTERPOLATORS)
    def test_linear_gradient(self, interp: InterpolationAlgorithm) -> None:
        mesh = build_mesh_from_func(*COARSE_MESH, linear_gradient)
        err = rmse(interp, mesh, linear_gradient, n_samples=200)
        key = _interp_key(interp)
        assert err < EXPECTED_ACCURACY["linear"][key], f"{key} RMSE {err:.4f}"

    @pytest.mark.parametrize("interp", INTERPOLATORS)
    def test_radial_coarse_mesh(self, interp: InterpolationAlgorithm) -> None:
        func = _radial100
        mesh = build_mesh_from_func(*COARSE_MESH, func)
        err = rmse(interp, mesh, func, n_samples=200)
        key = _interp_key(interp)
        assert err < EXPECTED_ACCURACY["radial_coarse"][key], f"{key} RMSE {err:.4f}"

    @pytest.mark.parametrize("interp", INTERPOLATORS)
    def test_radial_fine_mesh(self, interp: InterpolationAlgorithm) -> None:
        func = _radial100
        mesh = build_mesh_from_func(*FINE_MESH, func)
        err = rmse(interp, mesh, func, n_samples=200)
        key = _interp_key(interp)
        assert err < EXPECTED_ACCURACY["radial_fine"][key], f"{key} RMSE {err:.4f}"


class TestInterpolationEdgeCases:
    def test_single_cell_mesh(self) -> None:
        """2x2 grid — interpolation should still produce reasonable results."""
        m = Mesh(100.0, 100.0, 100.0)
        m.reset_offsets()
        m[0, 0] = dataclasses.replace(m[0, 0], offset_x=10.0, offset_y=10.0)
        m[0, 1] = dataclasses.replace(m[0, 1], offset_x=10.0, offset_y=10.0)
        m[1, 0] = dataclasses.replace(m[1, 0], offset_x=20.0, offset_y=20.0)
        m[1, 1] = dataclasses.replace(m[1, 1], offset_x=20.0, offset_y=20.0)

        for interp in [BilinearInterpolation(), BicubicInterpolation()]:
            ox, oy = interp.interpolate(m, 50.0, 50.0)
            assert 14.0 <= ox <= 16.0
            assert 14.0 <= oy <= 16.0

    def test_zero_offset_recovery(self) -> None:
        """All zeros — should return zeros everywhere."""
        m = Mesh(200.0, 200.0, 50.0)
        m.reset_offsets()

        for param in INTERPOLATORS:
            interp = param.values[0]
            if hasattr(interp, "_mesh_hash"):
                interp._mesh_hash = 0  # force cache rebuild
            ox, oy = interp.interpolate(m, 50.0, 50.0)
            assert abs(ox) < 1e-10
            assert abs(oy) < 1e-10

    def test_interpolate_at_node(self) -> None:
        """Interpolating at a mesh node should return the exact offset."""
        m = Mesh(200.0, 200.0, 50.0)
        m.reset_offsets()
        # Set offset at grid node (row=2, col=1): x=50, y=100
        m[2, 1] = dataclasses.replace(m[2, 1], offset_x=7.5, offset_y=-3.2)

        for interp in [BilinearInterpolation(), BicubicInterpolation()]:
            ox, oy = interp.interpolate(m, 50.0, 100.0)
            assert abs(ox - 7.5) < 1e-6
            assert abs(oy - (-3.2)) < 1e-6


class TestSinusoidalWarp:
    """Sinusoidal warp is more challenging — tests extrapolation behaviour."""

    @pytest.mark.parametrize(
        "interp",
        [
            pytest.param(BilinearInterpolation(), id="bilinear"),
            pytest.param(BicubicInterpolation(), id="bicubic"),
            pytest.param(ThinPlateSplineInterpolation(), id="tps"),
            pytest.param(RBFInterpolation(kernel="gaussian", epsilon=0.03), id="rbf"),
        ],
    )
    def test_sinusoidal_rmse_bounded(self, interp: InterpolationAlgorithm) -> None:
        func = sinusoidal_warp
        mesh = build_mesh_from_func(9, 9, 200.0, 200.0, func)
        err = rmse(interp, mesh, func, n_samples=200)
        # Sinusoidal is high-frequency; expect reasonable but not perfect accuracy
        assert err < 3.0, f"{err:.4f} >= 3.0"
