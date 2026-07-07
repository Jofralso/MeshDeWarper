"""Thin Plate Spline interpolation for distortion mesh correction."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from scipy.interpolate import RBFInterpolator

from cura_xy_calibration.interpolation.base import InterpolationAlgorithm

if TYPE_CHECKING:
    from cura_xy_calibration.core.mesh import Mesh

logger = logging.getLogger(__name__)


class ThinPlateSplineInterpolation(InterpolationAlgorithm):
    """Thin Plate Spline interpolation using scipy's RBF with thin-plate kernel.

    Provides smooth global interpolation suitable for complex distortion
    patterns. Caches the interpolator and rebuilds when the mesh changes.
    """

    def __init__(self, smoothing: float = 0.0):
        self._smoothing = smoothing
        self._interp_x: RBFInterpolator | None = None
        self._interp_y: RBFInterpolator | None = None
        self._mesh_hash: int = 0

    def interpolate(self, mesh: Mesh, x: float, y: float) -> tuple[float, float]:
        self._ensure_interpolators(mesh)
        assert self._interp_x is not None
        assert self._interp_y is not None

        pt = np.array([[x, y]])
        off_x = float(self._interp_x(pt).flat[0])
        off_y = float(self._interp_y(pt).flat[0])
        return (off_x, off_y)

    def _ensure_interpolators(self, mesh: Mesh) -> None:
        """Rebuild interpolators if mesh has changed."""
        current_hash = id(mesh)
        if self._interp_x is not None and self._mesh_hash == current_hash:
            return

        points = np.array([[p.x, p.y] for p in mesh])
        offsets_x = np.array([p.offset_x for p in mesh])
        offsets_y = np.array([p.offset_y for p in mesh])

        if len(points) < 4:
            logger.warning("TPS interpolation needs at least 4 points")
            self._interp_x = _ZeroInterpolator()
            self._interp_y = _ZeroInterpolator()
            self._mesh_hash = current_hash
            return

        self._interp_x = RBFInterpolator(
            points,
            offsets_x,
            kernel="thin_plate_spline",
            smoothing=self._smoothing,
        )
        self._interp_y = RBFInterpolator(
            points,
            offsets_y,
            kernel="thin_plate_spline",
            smoothing=self._smoothing,
        )
        self._mesh_hash = current_hash
        logger.debug("TPS interpolators rebuilt (%d points)", len(points))

    def name(self) -> str:
        return "thin_plate_spline"


class _ZeroInterpolator:
    """Fallback interpolator returning zero offsets."""

    def __call__(self, pt: np.ndarray) -> np.ndarray:
        return np.zeros(pt.shape[0])
