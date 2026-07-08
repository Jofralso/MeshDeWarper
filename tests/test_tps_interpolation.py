"""Tests for ThinPlateSplineInterpolation."""

from __future__ import annotations

from mesh_de_warper.core.mesh import Mesh
from mesh_de_warper.core.point import Point
from mesh_de_warper.interpolation.tps import ThinPlateSplineInterpolation


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
        ox1, _ = interp.interpolate(mesh, 10.0, 10.0)
        ox2, _ = interp.interpolate(mesh, 20.0, 20.0)
        assert isinstance(ox1, float)
        assert isinstance(ox2, float)

    def test_name(self) -> None:
        interp = ThinPlateSplineInterpolation()
        assert interp.name() == "thin_plate_spline"

    def test_fewer_than_four_points(self) -> None:
        mesh = Mesh(width=10.0, height=10.0, spacing=10.0)
        interp = ThinPlateSplineInterpolation()
        ox, oy = interp.interpolate(mesh, 5.0, 5.0)
        assert ox == 0.0
        assert oy == 0.0

    def test_caching_different_mesh_object(self) -> None:
        interp = ThinPlateSplineInterpolation()
        mesh_a = Mesh(width=60.0, height=60.0, spacing=10.0)
        mesh_b = Mesh(width=60.0, height=60.0, spacing=10.0)
        from mesh_de_warper.core.point import Point
        mesh_b[3, 3] = Point(x=30.0, y=30.0, offset_x=1.0, offset_y=1.0)
        ox_a, oy_a = interp.interpolate(mesh_a, 30.0, 30.0)
        ox_b, oy_b = interp.interpolate(mesh_b, 30.0, 30.0)
        assert (ox_a, oy_a) != (ox_b, oy_b)
