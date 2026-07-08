"""Tests for Point data type."""

from __future__ import annotations

import pytest

from mesh_de_warper.core.point import Point


class TestPoint:
    def test_default_offset(self) -> None:
        p = Point(x=10.0, y=20.0)
        assert p.x == 10.0
        assert p.y == 20.0
        assert p.offset_x == 0.0
        assert p.offset_y == 0.0
        assert p.actual_x == 10.0
        assert p.actual_y == 20.0

    def test_with_offset(self) -> None:
        p = Point(x=10.0, y=20.0, offset_x=0.5, offset_y=-0.3)
        assert p.actual_x == 10.5
        assert p.actual_y == 19.7

    def test_magnitude(self) -> None:
        p = Point(x=0.0, y=0.0, offset_x=3.0, offset_y=4.0)
        assert p.magnitude == 5.0

    def test_with_offset_returns_new_point(self) -> None:
        p = Point(x=10.0, y=20.0)
        p2 = p.with_offset(offset_x=1.0, offset_y=2.0)
        assert p2.offset_x == 1.0
        assert p2.offset_y == 2.0
        assert p.offset_x == 0.0  # original unchanged

    def test_as_tuple(self) -> None:
        p = Point(x=10.0, y=20.0)
        assert p.as_tuple() == (10.0, 20.0)

    def test_as_actual_tuple(self) -> None:
        p = Point(x=10.0, y=20.0, offset_x=0.5, offset_y=-0.3)
        assert p.as_actual_tuple() == (10.5, 19.7)

    def test_distance_to(self) -> None:
        p1 = Point(x=0.0, y=0.0)
        p2 = Point(x=3.0, y=4.0)
        assert p1.distance_to(p2) == 5.0

    def test_interpolate_to(self) -> None:
        p1 = Point(x=0.0, y=0.0, offset_x=0.0, offset_y=0.0)
        p2 = Point(x=10.0, y=10.0, offset_x=2.0, offset_y=4.0)
        mid = p1.interpolate_to(p2, 0.5)
        assert mid.x == 5.0
        assert mid.y == 5.0
        assert mid.offset_x == 1.0
        assert mid.offset_y == 2.0

    def test_interpolate_to_ends(self) -> None:
        p1 = Point(x=0.0, y=0.0)
        p2 = Point(x=10.0, y=10.0, offset_x=2.0, offset_y=4.0)
        assert p1.interpolate_to(p2, 0.0) == p1
        assert p1.interpolate_to(p2, 1.0) == p2

    def test_frozen_dataclass(self) -> None:
        p = Point(x=1.0, y=2.0)
        with pytest.raises(AttributeError):
            p.x = 3.0  # type: ignore[misc]

    def test_repr(self) -> None:
        p = Point(x=1.0, y=2.0, offset_x=0.5, offset_y=-0.3)
        r = repr(p)
        assert "Point" in r
        assert "1.0" in r
        assert "2.0" in r
