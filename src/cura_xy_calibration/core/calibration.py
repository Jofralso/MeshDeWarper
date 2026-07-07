"""Calibration — orchestrates distortion correction."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Self

from cura_xy_calibration.core.mesh import Mesh
from cura_xy_calibration.core.point import Point
from cura_xy_calibration.core.profile import CalibrationProfile
from cura_xy_calibration.interpolation.base import InterpolationAlgorithm

logger = logging.getLogger(__name__)


@dataclass
class Calibration:
    """Orchestrates distortion correction for a printer bed.

    Attributes:
        mesh: The distortion mesh.
        interpolation: The interpolation algorithm.
    """

    mesh: Mesh
    interpolation: InterpolationAlgorithm

    @classmethod
    def for_bed(
        cls,
        width: float,
        height: float,
        spacing: float,
        interpolation: InterpolationAlgorithm,
    ) -> Self:
        """Create a Calibration for a bed of given dimensions."""
        mesh = Mesh(width=width, height=height, spacing=spacing)
        return cls(mesh=mesh, interpolation=interpolation)

    def correct_point(self, x: float, y: float) -> tuple[float, float]:
        """Return corrected (x, y) by interpolating the distortion mesh."""
        cx, cy = self.interpolation.interpolate(self.mesh, x, y)
        return (x + cx, y + cy)

    def offset_at(self, x: float, y: float) -> tuple[float, float]:
        """Return the distortion offset at a given nominal position."""
        return self.interpolation.interpolate(self.mesh, x, y)

    def residuals(self) -> list[float]:
        """Return list of offset magnitudes for all mesh points."""
        return [p.magnitude for p in self.mesh]

    def max_residual(self) -> float:
        """Return the maximum offset magnitude across the mesh."""
        return max(self.residuals(), default=0.0)

    def mean_residual(self) -> float:
        """Return the mean offset magnitude across the mesh."""
        residuals = self.residuals()
        return sum(residuals) / len(residuals) if residuals else 0.0

    def to_profile(self) -> CalibrationProfile:
        """Export the current calibration state to a profile."""
        from cura_xy_calibration.core.profile import CalibrationProfile

        offsets = {(p.x, p.y): (p.offset_x, p.offset_y) for p in self.mesh}
        return CalibrationProfile(
            printer="",
            bed_width=self.mesh.width,
            bed_height=self.mesh.height,
            spacing=self.mesh.spacing,
            interpolation=self.interpolation.name(),
            offsets=offsets,
        )

    @classmethod
    def from_profile(
        cls,
        profile: CalibrationProfile,
        interpolation: InterpolationAlgorithm,
    ) -> Self:
        """Restore a Calibration from a profile."""
        mesh = Mesh(
            width=profile.bed_width,
            height=profile.bed_height,
            spacing=profile.spacing,
        )
        for p in mesh:
            key = (round(p.x, 6), round(p.y, 6))
            off = profile.offsets.get(key, (0.0, 0.0))
            mesh.points[int(p.y / profile.spacing)][int(p.x / profile.spacing)] = Point(
                x=p.x,
                y=p.y,
                offset_x=off[0],
                offset_y=off[1],
            )
        return cls(mesh=mesh, interpolation=interpolation)
