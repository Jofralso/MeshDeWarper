"""Bilinear interpolation for distortion mesh correction."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mesh_de_warper.interpolation.base import InterpolationAlgorithm

if TYPE_CHECKING:  # pragma: no cover
    from mesh_de_warper.core.mesh import Mesh

logger = logging.getLogger(__name__)


class BilinearInterpolation(InterpolationAlgorithm):
    """Bilinear interpolation over the rectangular mesh.

    Computes the offset at any point by bilinear interpolation of
    the four surrounding mesh points. Handles boundary clamping.
    """

    def interpolate(self, mesh: Mesh, x: float, y: float) -> tuple[float, float]:
        """Interpolate offset at (x, y) using bilinear interpolation."""
        if mesh.rows < 2 or mesh.cols < 2:  # pragma: no cover
            return (0.0, 0.0)  # pragma: no cover

        mesh_min_x, mesh_min_y, mesh_max_x, mesh_max_y = mesh.get_bounds()

        # Clamp to mesh boundaries
        cx = max(mesh_min_x, min(x, mesh_max_x))
        cy = max(mesh_min_y, min(y, mesh_max_y))

        # Find grid cell indices
        col = int((cx - mesh_min_x) / mesh.spacing)
        row = int((cy - mesh_min_y) / mesh.spacing)

        # Clamp to valid cell range
        col = max(0, min(col, mesh.cols - 2))
        row = max(0, min(row, mesh.rows - 2))

        # Get the four corners of the cell
        p00 = mesh[row, col]
        p10 = mesh[row, col + 1]
        p01 = mesh[row + 1, col]
        p11 = mesh[row + 1, col + 1]

        # Normalised coordinates within the cell (0..1)
        x_frac = (cx - p00.x) / mesh.spacing if mesh.spacing > 0 else 0.0
        y_frac = (cy - p00.y) / mesh.spacing if mesh.spacing > 0 else 0.0

        # Bilinear interpolation of offsets
        off_x = (
            p00.offset_x * (1 - x_frac) * (1 - y_frac)
            + p10.offset_x * x_frac * (1 - y_frac)
            + p01.offset_x * (1 - x_frac) * y_frac
            + p11.offset_x * x_frac * y_frac
        )
        off_y = (
            p00.offset_y * (1 - x_frac) * (1 - y_frac)
            + p10.offset_y * x_frac * (1 - y_frac)
            + p01.offset_y * (1 - x_frac) * y_frac
            + p11.offset_y * x_frac * y_frac
        )

        return (off_x, off_y)

    def name(self) -> str:
        """Return display name of the interpolation method."""
        return "bilinear"
