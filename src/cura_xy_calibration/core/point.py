"""Point data type for 2D coordinates with calibration offsets."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    """A 2D point with optional distortion offset.

    The `nominal` coordinates represent the intended position.
    The `actual` coordinates represent the measured/calibrated position.
    The offset is derived as `actual - nominal`.

    Attributes:
        x: Nominal X coordinate (mm).
        y: Nominal Y coordinate (mm).
        offset_x: Calibrated offset in X (mm). Defaults to 0.0.
        offset_y: Calibrated offset in Y (mm). Defaults to 0.0.
    """

    x: float
    y: float
    offset_x: float = 0.0
    offset_y: float = 0.0

    @property
    def actual_x(self) -> float:
        """Measured/calibrated X coordinate (nominal + offset)."""
        return self.x + self.offset_x

    @property
    def actual_y(self) -> float:
        """Measured/calibrated Y coordinate (nominal + offset)."""
        return self.y + self.offset_y

    @property
    def magnitude(self) -> float:
        """Magnitude of the offset vector."""
        return math.hypot(self.offset_x, self.offset_y)

    def with_offset(self, offset_x: float, offset_y: float) -> Point:
        """Return a new Point with the given offset applied."""
        return Point(x=self.x, y=self.y, offset_x=offset_x, offset_y=offset_y)

    def as_tuple(self) -> tuple[float, float]:
        """Return nominal coordinates as a tuple."""
        return (self.x, self.y)

    def as_actual_tuple(self) -> tuple[float, float]:
        """Return actual coordinates as a tuple."""
        return (self.actual_x, self.actual_y)

    def distance_to(self, other: Point) -> float:
        """Euclidean distance between nominal positions."""
        return math.hypot(self.x - other.x, self.y - other.y)

    def interpolate_to(self, other: Point, t: float) -> Point:
        """Linearly interpolate between two points by factor t (0..1)."""
        return Point(
            x=self.x + (other.x - self.x) * t,
            y=self.y + (other.y - self.y) * t,
            offset_x=self.offset_x + (other.offset_x - self.offset_x) * t,
            offset_y=self.offset_y + (other.offset_y - self.offset_y) * t,
        )
