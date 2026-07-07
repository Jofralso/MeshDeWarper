"""Tests for BicubicInterpolation."""

from __future__ import annotations

import numpy as np

from cura_xy_calibration.core.mesh import Mesh
from cura_xy_calibration.core.point import Point
from cura_xy_calibration.interpolation.bicubic import BicubicInterpolation


class TestBicubicInterpolation:
    def test_small_grid_falls_back(self) -> None:
        mesh = Mesh(width=20.0, height=20.0, spacing=10.0)  # 3x3 grid
        interp = BicubicInterpolation()
        ox, oy = interp.interpolate(mesh, 5.0, 5.0)
        assert isinstance(ox, float)
        assert isinstance(oy, float)

    def test_name(self) -> None:
        interp = BicubicInterpolation()
        assert interp.name() == "bicubic"

    def test_large_grid(self) -> None:
        mesh = Mesh(width=100.0, height=100.0, spacing=10.0)
        mesh[3, 3] = Point(x=30.0, y=30.0, offset_x=2.0, offset_y=3.0)
        interp = BicubicInterpolation()
        ox, oy = interp.interpolate(mesh, 35.0, 35.0)
        assert isinstance(ox, float)
        assert isinstance(oy, float)

    def test_cubic_kernel(self) -> None:
        interp = BicubicInterpolation()
        result = interp._cubic(0.0, 1.0, 2.0, 3.0, 0.5)
        assert abs(result - 1.5) < 1e-6  # linear mid

    def test_bicubic_linear_field(self) -> None:
        p = np.array(
            [
                [0.0, 1.0, 2.0, 3.0],
                [1.0, 2.0, 3.0, 4.0],
                [2.0, 3.0, 4.0, 5.0],
                [3.0, 4.0, 5.0, 6.0],
            ]
        )
        interp = BicubicInterpolation()
        result = interp._bicubic(p, 0.5, 0.5)
        assert abs(result - 3.0) < 1e-6  # mid of bilinear field
