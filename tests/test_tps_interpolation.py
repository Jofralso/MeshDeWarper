"""Tests for ThinPlateSplineInterpolation."""

from __future__ import annotations

from cura_xy_calibration.core.mesh import Mesh
from cura_xy_calibration.core.point import Point
from cura_xy_calibration.interpolation.tps import ThinPlateSplineInterpolation


class TestThinPlateSplineInterpolation:
    def test_small_grid_falls_back(self) -> None:
        mesh = Mesh(width=10.0, height=10.0, spacing=5.0)  # 3x3 grid
        interp = ThinPlateSplineInterpolation()
        ox, oy = interp.interpolate(mesh, 5.0, 5.0)
        assert ox == 0.0
        assert oy == 0.0

    def test_with_offsets(self) -> None:
        mesh = Mesh(width=60.0, height=60.0, spacing=10.0)
        mesh[3, 3] = Point(x=30.0, y=30.0, offset_x=2.0, offset_y=3.0)
        interp = ThinPlateSplineInterpolation(smoothing=0.1)
        ox, oy = interp.interpolate(mesh, 30.0, 30.0)
        assert abs(ox - 2.0) < 0.5
        assert abs(oy - 3.0) < 0.5

    def test_caching(self) -> None:
        mesh = Mesh(width=60.0, height=60.0, spacing=10.0)
        interp = ThinPlateSplineInterpolation()
        ox1, oy1 = interp.interpolate(mesh, 10.0, 10.0)
        ox2, oy2 = interp.interpolate(mesh, 20.0, 20.0)
        assert isinstance(ox1, float)
        assert isinstance(ox2, float)

    def test_name(self) -> None:
        interp = ThinPlateSplineInterpolation()
        assert interp.name() == "thin_plate_spline"
