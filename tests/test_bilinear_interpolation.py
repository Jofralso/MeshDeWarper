"""Tests for BilinearInterpolation."""

from __future__ import annotations

from cura_xy_calibration.core.mesh import Mesh
from cura_xy_calibration.core.point import Point
from cura_xy_calibration.interpolation.bilinear import BilinearInterpolation


class TestBilinearInterpolation:
    def test_at_grid_point(self) -> None:
        mesh = Mesh(width=20.0, height=20.0, spacing=10.0)
        mesh[0, 0] = Point(x=0.0, y=0.0, offset_x=1.0, offset_y=2.0)
        interp = BilinearInterpolation()
        ox, oy = interp.interpolate(mesh, 0.0, 0.0)
        assert ox == 1.0
        assert oy == 2.0

    def test_at_grid_centre(self) -> None:
        mesh = Mesh(width=20.0, height=20.0, spacing=10.0)
        mesh[0, 0] = Point(x=0.0, y=0.0, offset_x=0.0, offset_y=0.0)
        mesh[0, 1] = Point(x=10.0, y=0.0, offset_x=2.0, offset_y=0.0)
        mesh[1, 0] = Point(x=0.0, y=10.0, offset_x=0.0, offset_y=2.0)
        mesh[1, 1] = Point(x=10.0, y=10.0, offset_x=2.0, offset_y=2.0)
        interp = BilinearInterpolation()
        ox, oy = interp.interpolate(mesh, 5.0, 5.0)
        assert abs(ox - 1.0) < 0.001
        assert abs(oy - 1.0) < 0.001

    def test_out_of_bounds_clamps(self) -> None:
        mesh = Mesh(width=20.0, height=20.0, spacing=10.0)
        mesh[0, 0] = Point(x=0.0, y=0.0, offset_x=1.0, offset_y=1.0)
        interp = BilinearInterpolation()
        # Point beyond mesh bounds should clamp
        ox, oy = interp.interpolate(mesh, 100.0, 100.0)
        assert isinstance(ox, float)
        assert isinstance(oy, float)

    def test_small_grid(self) -> None:
        mesh = Mesh(width=5.0, height=5.0, spacing=10.0)
        interp = BilinearInterpolation()
        ox, oy = interp.interpolate(mesh, 2.0, 2.0)
        assert ox == 0.0
        assert oy == 0.0

    def test_name(self) -> None:
        interp = BilinearInterpolation()
        assert interp.name() == "bilinear"

    def test_very_small_spacing_handling(self) -> None:
        mesh = Mesh(width=100.0, height=100.0, spacing=0.01)
        assert mesh.rows <= 1001  # capped
        assert mesh.cols <= 1001
        interp = BilinearInterpolation()
        ox, oy = interp.interpolate(mesh, 50.0, 50.0)
        assert ox == 0.0
        assert oy == 0.0
