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

    Uses a 4x4 neighbourhood and cubic convolution kernel (Catmull-Rom)
    for smoother results than bilinear interpolation.  Falls back to
    bilinear when the mesh is too small for a 4x4 neighbourhood.
    """

    def interpolate(self, mesh: Mesh, x: float, y: float) -> tuple[float, float]:
        if mesh.rows < 4 or mesh.cols < 4:
            return _bilinear_fallback(mesh, x, y)

        mesh_min_x, mesh_min_y, mesh_max_x, mesh_max_y = mesh.get_bounds()
        cx = max(mesh_min_x, min(x, mesh_max_x))
        cy = max(mesh_min_y, min(y, mesh_max_y))

        spacing = mesh.spacing

        # Cell containing the query point
        col = int((cx - mesh_min_x) / spacing)
        row = int((cy - mesh_min_y) / spacing)

        # Clamp cell index to valid interior
        col = max(0, min(col, mesh.cols - 2))
        row = max(0, min(row, mesh.rows - 2))

        # Fall back to bilinear at boundary cells (Catmull-Rom edge mirroring
        # introduces errors for linear functions)
        if col == 0 or col >= mesh.cols - 3 or row == 0 or row >= mesh.rows - 3:
            return _bilinear_fallback(mesh, cx, cy)

        # Fractional position within the cell [0, 1]
        x_frac = (cx - (mesh_min_x + col * spacing)) / spacing
        y_frac = (cy - (mesh_min_y + row * spacing)) / spacing

        # 4x4 neighbourhood centred on (col, row)
        ox = np.zeros((4, 4))
        oy = np.zeros((4, 4))
        for i in range(4):
            for j in range(4):
                p = mesh[row + i - 1, col + j - 1]
                ox[i, j] = p.offset_x
                oy[i, j] = p.offset_y

        off_x = self._bicubic(ox, x_frac, y_frac)
        off_y = self._bicubic(oy, x_frac, y_frac)

        return (off_x, off_y)

    def _bicubic(self, p: np.ndarray, x: float, y: float) -> float:
        """Bicubic interpolation on a 4x4 patch using Catmull-Rom.

        First interpolates along Y (columns) at parameter *y*, then
        interpolates the resulting 4 values along X at parameter *x*.
        """
        arr = np.zeros(4)
        for j in range(4):
            arr[j] = self._cubic(p[0, j], p[1, j], p[2, j], p[3, j], y)
        return self._cubic(arr[0], arr[1], arr[2], arr[3], x)

    @staticmethod
    def _cubic(v0: float, v1: float, v2: float, v3: float, t: float) -> float:
        """Catmull-Rom cubic convolution (t in [0, 1])."""
        t2 = t * t
        t3 = t2 * t
        return (
            (-0.5 * v0 + 1.5 * v1 - 1.5 * v2 + 0.5 * v3) * t3
            + (v0 - 2.5 * v1 + 2.0 * v2 - 0.5 * v3) * t2
            + (-0.5 * v0 + 0.5 * v2) * t
            + v1
        )

    def name(self) -> str:
        return "bicubic"


def _bilinear_fallback(mesh: Mesh, x: float, y: float) -> tuple[float, float]:
    """Fallback to bilinear when bicubic neighbourhood is too small."""
    from cura_xy_calibration.interpolation.bilinear import BilinearInterpolation

    return BilinearInterpolation().interpolate(mesh, x, y)
