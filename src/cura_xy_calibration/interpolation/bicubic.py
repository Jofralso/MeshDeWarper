"""Bicubic interpolation for distortion mesh correction."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from cura_xy_calibration.interpolation.base import InterpolationAlgorithm

if TYPE_CHECKING:
    from cura_xy_calibration.core.mesh import Mesh

logger = logging.getLogger(__name__)


class BicubicInterpolation(InterpolationAlgorithm):
    """Bicubic interpolation over the rectangular mesh.

    Uses a 4x4 neighbourhood and cubic convolution kernel for
    smoother results than bilinear interpolation.
    """

    def interpolate(self, mesh: Mesh, x: float, y: float) -> tuple[float, float]:
        if mesh.rows < 4 or mesh.cols < 4:
            return BilinearFallback().interpolate(mesh, x, y)

        mesh_min_x, mesh_min_y, mesh_max_x, mesh_max_y = mesh.get_bounds()
        cx = max(mesh_min_x, min(x, mesh_max_x))
        cy = max(mesh_min_y, min(y, mesh_max_y))

        spacing = mesh.spacing
        col = int((cx - mesh_min_x) / spacing)
        row = int((cy - mesh_min_y) / spacing)

        # Clamp so we have 4x4 neighbourhood
        col = max(1, min(col, mesh.cols - 3))
        row = max(1, min(row, mesh.rows - 3))

        col -= 1
        row -= 1

        x_frac = (cx - (mesh_min_x + (col + 1) * spacing)) / spacing
        y_frac = (cy - (mesh_min_y + (row + 1) * spacing)) / spacing

        # Extract 4x4 offset arrays
        ox = np.zeros((4, 4))
        oy = np.zeros((4, 4))
        for i in range(4):
            for j in range(4):
                p = mesh[row + i, col + j]
                ox[i, j] = p.offset_x
                oy[i, j] = p.offset_y

        off_x = self._cubic_interpolate(ox, x_frac, y_frac)
        off_y = self._cubic_interpolate(oy, x_frac, y_frac)

        return (off_x, off_y)

    def _cubic_interpolate(self, p: np.ndarray, x: float, y: float) -> float:
        """Bicubic interpolation on a 4x4 patch."""
        arr = np.zeros(4)
        for i in range(4):
            arr[i] = self._cubic_convolution(p[i, 0], p[i, 1], p[i, 2], p[i, 3], y)
        return self._cubic_convolution(arr[0], arr[1], arr[2], arr[3], x)

    @staticmethod
    def _cubic_convolution(v0: float, v1: float, v2: float, v3: float, t: float) -> float:
        """Cubic convolution interpolation (Catmull-Rom)."""
        t2 = t * t
        t3 = t2 * t
        a = -0.5 * v0 + 1.5 * v1 - 1.5 * v2 + 0.5 * v3
        b = v0 - 2.5 * v1 + 2.0 * v2 - 0.5 * v3
        c = -0.5 * v0 + 0.5 * v2
        d = v1
        return a * t3 + b * t2 + c * t + d

    def name(self) -> str:
        return "bicubic"


class BilinearFallback(InterpolationAlgorithm):
    """Fallback to bilinear when bicubic neighbourhood is too small."""

    def interpolate(self, mesh: Mesh, x: float, y: float) -> tuple[float, float]:
        from cura_xy_calibration.interpolation.bilinear import BilinearInterpolation

        return BilinearInterpolation().interpolate(mesh, x, y)

    def name(self) -> str:
        return "bilinear_fallback"
