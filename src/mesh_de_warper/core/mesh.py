"""Distortion mesh — a 2D grid of Points with calibration offsets."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field

from mesh_de_warper.core.point import Point

logger = logging.getLogger(__name__)


@dataclass
class Mesh:
    """A rectangular grid of points representing the calibration mesh.

    The mesh spans the printable area with uniform spacing. Each point
    stores a nominal position and a calibrated offset.

    Attributes:
        width: Bed width in mm.
        height: Bed height in mm.
        spacing: Grid spacing in mm.
        points: 2D list of points indexed as [row][col].
    """

    width: float
    height: float
    spacing: float
    points: list[list[Point]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Build grid if no points were provided."""
        if not self.points:
            self._build_grid()

    def _build_grid(self) -> None:
        """Build the initial nominal grid with zero offsets."""
        spacing = max(self.spacing, self.width / 1000, self.height / 1000, 0.1)
        cols = max(2, int(self.width / spacing) + 1)
        rows = max(2, int(self.height / spacing) + 1)
        self.points = [
            [Point(x=col * self.spacing, y=row * self.spacing) for col in range(cols)]
            for row in range(rows)
        ]

    @property
    def rows(self) -> int:
        """Number of rows in the grid."""
        return len(self.points)

    @property
    def cols(self) -> int:
        """Number of columns in the grid."""
        return len(self.points[0]) if self.points else 0

    @property
    def num_points(self) -> int:
        """Total number of points in the grid."""
        return self.rows * self.cols

    def __getitem__(self, key: tuple[int, int]) -> Point:
        """Access a point by (row, col) index."""
        row, col = key
        return self.points[row][col]

    def __setitem__(self, key: tuple[int, int], point: Point) -> None:
        """Set a point at (row, col) index."""
        row, col = key
        self.points[row][col] = point

    def __iter__(self) -> Iterator[Point]:
        """Iterate over all points in row-major order."""
        for row in self.points:
            yield from row

    def iter_with_index(self) -> Iterator[tuple[int, int, Point]]:
        """Iterate over (row, col, point) in row-major order."""
        for row_idx, row in enumerate(self.points):
            for col_idx, point in enumerate(row):
                yield row_idx, col_idx, point

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Return (min_x, min_y, max_x, max_y) of nominal positions."""
        min_x = min(p.x for p in self)
        min_y = min(p.y for p in self)
        max_x = max(p.x for p in self)
        max_y = max(p.y for p in self)
        return (min_x, min_y, max_x, max_y)

    def reset_offsets(self) -> None:
        """Reset all calibration offsets to zero."""
        for row in self.points:
            for col, point in enumerate(row):
                row[col] = Point(x=point.x, y=point.y)

    def apply_uniform_offset(self, offset_x: float, offset_y: float) -> None:
        """Apply a uniform offset to all points."""
        for row in self.points:
            for col, point in enumerate(row):
                row[col] = Point(
                    x=point.x,
                    y=point.y,
                    offset_x=point.offset_x + offset_x,
                    offset_y=point.offset_y + offset_y,
                )

    def clone(self) -> Mesh:
        """Create a deep copy of this mesh."""
        return Mesh(
            width=self.width,
            height=self.height,
            spacing=self.spacing,
            points=[[p for p in row] for row in self.points],
        )
