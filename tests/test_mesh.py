"""Tests for Mesh data type."""

from __future__ import annotations

from cura_xy_calibration.core.mesh import Mesh
from cura_xy_calibration.core.point import Point


class TestMesh:
    def test_auto_build_grid(self) -> None:
        m = Mesh(width=100.0, height=80.0, spacing=10.0)
        assert m.rows == 9  # 0, 10, 20, ..., 80
        assert m.cols == 11  # 0, 10, 20, ..., 100
        assert m.num_points == 99

    def test_minimum_grid_size(self) -> None:
        m = Mesh(width=5.0, height=5.0, spacing=10.0)
        assert m.rows >= 2
        assert m.cols >= 2

    def test_getitem_setitem(self) -> None:
        m = Mesh(width=20.0, height=20.0, spacing=10.0)
        p = m[0, 0]
        assert p.x == 0.0
        assert p.y == 0.0
        assert p.offset_x == 0.0

        new_p = Point(x=0.0, y=0.0, offset_x=1.0, offset_y=2.0)
        m[0, 0] = new_p
        assert m[0, 0].offset_x == 1.0

    def test_iterate_points(self) -> None:
        m = Mesh(width=20.0, height=20.0, spacing=10.0)
        points = list(m)
        assert len(points) == 9  # 3x3 grid
        assert all(isinstance(p, Point) for p in points)

    def test_iter_with_index(self) -> None:
        m = Mesh(width=20.0, height=20.0, spacing=10.0)
        indices = list(m.iter_with_index())
        assert len(indices) == 9
        assert indices[0] == (0, 0, m[0, 0])
        assert indices[4] == (1, 1, m[1, 1])

    def test_get_bounds(self) -> None:
        m = Mesh(width=100.0, height=80.0, spacing=10.0)
        min_x, min_y, max_x, max_y = m.get_bounds()
        assert min_x == 0.0
        assert min_y == 0.0
        assert max_x == 100.0
        assert max_y == 80.0

    def test_reset_offsets(self) -> None:
        m = Mesh(width=20.0, height=20.0, spacing=10.0)
        m[0, 0] = Point(x=0.0, y=0.0, offset_x=5.0, offset_y=5.0)
        m.reset_offsets()
        assert m[0, 0].offset_x == 0.0
        assert m[0, 0].offset_y == 0.0

    def test_uniform_offset(self) -> None:
        m = Mesh(width=20.0, height=20.0, spacing=10.0)
        m[0, 0] = Point(x=0.0, y=0.0, offset_x=1.0, offset_y=2.0)
        m.apply_uniform_offset(0.5, -0.5)
        assert m[0, 0].offset_x == 1.5
        assert m[0, 0].offset_y == 1.5

    def test_clone(self) -> None:
        m = Mesh(width=100.0, height=100.0, spacing=10.0)
        m[5, 5] = Point(x=50.0, y=50.0, offset_x=1.0, offset_y=2.0)
        cloned = m.clone()
        assert cloned.width == m.width
        assert cloned.height == m.height
        assert cloned[5, 5].offset_x == 1.0
        # Verify deep copy
        m[5, 5] = Point(x=50.0, y=50.0)
        assert cloned[5, 5].offset_x == 1.0

    def test_custom_points(self) -> None:
        points = [
            [Point(x=0.0, y=0.0), Point(x=10.0, y=0.0)],
            [Point(x=0.0, y=10.0), Point(x=10.0, y=10.0)],
        ]
        m = Mesh(width=10.0, height=10.0, spacing=10.0, points=points)
        assert m.rows == 2
        assert m.cols == 2
        assert m.num_points == 4
