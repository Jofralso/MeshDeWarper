"""Tests for RBFInterpolation."""

from __future__ import annotations

import pytest

from mesh_de_warper.core.mesh import Mesh
from mesh_de_warper.core.point import Point
from mesh_de_warper.interpolation.rbf import SUPPORTED_KERNELS, RBFInterpolation


class TestRBFInterpolation:
    def test_supported_kernels(self) -> None:
        for kernel in SUPPORTED_KERNELS:
            interp = RBFInterpolation(kernel=kernel)
            assert interp.name() == f"rbf_{kernel}"

    def test_invalid_kernel(self) -> None:
        with pytest.raises(ValueError, match="Unsupported kernel"):
            RBFInterpolation(kernel="invalid_kernel")

    def test_small_grid_falls_back(self) -> None:
        mesh = Mesh(width=10.0, height=10.0, spacing=5.0)
        interp = RBFInterpolation()
        ox, oy = interp.interpolate(mesh, 5.0, 5.0)
        assert ox == 0.0
        assert oy == 0.0

    def test_with_offsets(self) -> None:
        mesh = Mesh(width=60.0, height=60.0, spacing=10.0)
        mesh[3, 3] = Point(x=30.0, y=30.0, offset_x=2.0, offset_y=3.0)
        interp = RBFInterpolation(kernel="multiquadric", smoothing=0.1)
        ox, oy = interp.interpolate(mesh, 30.0, 30.0)
        assert abs(ox - 2.0) < 1.0
        assert abs(oy - 3.0) < 1.0

    def test_caching(self) -> None:
        mesh = Mesh(width=60.0, height=60.0, spacing=10.0)
        interp = RBFInterpolation()
        ox1, _ = interp.interpolate(mesh, 10.0, 10.0)
        ox2, _ = interp.interpolate(mesh, 20.0, 20.0)
        assert isinstance(ox1, float)
        assert isinstance(ox2, float)

    def test_name_multiquadric(self) -> None:
        interp = RBFInterpolation(kernel="multiquadric")
        assert interp.name() == "rbf_multiquadric"

    def test_name_gaussian(self) -> None:
        interp = RBFInterpolation(kernel="gaussian")
        assert interp.name() == "rbf_gaussian"

    def test_fewer_than_four_points(self) -> None:
        mesh = Mesh(width=10.0, height=10.0, spacing=10.0)
        interp = RBFInterpolation()
        ox, oy = interp.interpolate(mesh, 5.0, 5.0)
        assert ox == 0.0
        assert oy == 0.0

    def test_caching_different_mesh_object(self) -> None:
        interp = RBFInterpolation()
        mesh_a = Mesh(width=60.0, height=60.0, spacing=10.0)
        mesh_b = Mesh(width=60.0, height=60.0, spacing=10.0)
        from mesh_de_warper.core.point import Point
        mesh_b[3, 3] = Point(x=30.0, y=30.0, offset_x=1.0, offset_y=1.0)
        ox_a, oy_a = interp.interpolate(mesh_a, 30.0, 30.0)
        ox_b, oy_b = interp.interpolate(mesh_b, 30.0, 30.0)
        # Different meshes should produce different results when offsets differ
        assert (ox_a, oy_a) != (ox_b, oy_b)

    def test_auto_epsilon_mesh(self) -> None:
        mesh = Mesh(width=60.0, height=60.0, spacing=10.0)
        interp = RBFInterpolation(kernel="multiquadric")
        ox, oy = interp.interpolate(mesh, 15.0, 15.0)
        assert isinstance(ox, float)
        assert isinstance(oy, float)

    def test_single_point_mesh_epsilon(self) -> None:
        mesh = Mesh(width=10.0, height=10.0, spacing=100.0)
        interp = RBFInterpolation(kernel="gaussian")
        ox, _ = interp.interpolate(mesh, 5.0, 5.0)
        assert isinstance(ox, float)
