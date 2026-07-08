"""Radial Basis Function interpolation for distortion mesh correction."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from scipy.interpolate import RBFInterpolator

from mesh_de_warper.interpolation.base import InterpolationAlgorithm

if TYPE_CHECKING:  # pragma: no cover
    from mesh_de_warper.core.mesh import Mesh

logger = logging.getLogger(__name__)

SUPPORTED_KERNELS = frozenset(
    {
        "multiquadric",
        "inverse_multiquadric",
        "gaussian",
        "linear",
        "cubic",
        "quintic",
        "thin_plate_spline",
    }
)


class RBFInterpolation(InterpolationAlgorithm):
    """Radial Basis Function interpolation with configurable kernel.

    Supports all scipy RBF kernels. Caches the interpolator and
    rebuilds when the mesh changes.

    Attributes:
        kernel: RBF kernel type (default: 'multiquadric').
        epsilon: Shape parameter (auto if None).
        smoothing: Regularisation parameter.
    """

    def __init__(
        self,
        kernel: str = "multiquadric",
        epsilon: float | None = None,
        smoothing: float = 0.0,
    ) -> None:
        if kernel not in SUPPORTED_KERNELS:
            msg = f"Unsupported kernel '{kernel}'. Choose from {sorted(SUPPORTED_KERNELS)}"
            raise ValueError(msg)
        self._kernel = kernel
        self._epsilon = epsilon
        self._smoothing = smoothing
        self._auto_epsilon = epsilon is None
        self._interp_x: RBFInterpolator | None = None
        self._interp_y: RBFInterpolator | None = None
        self._mesh_hash: int = 0

    def interpolate(self, mesh: Mesh, x: float, y: float) -> tuple[float, float]:
        """Interpolate offset at (x, y) using RBF interpolation."""
        self._ensure_interpolators(mesh)
        if self._interp_x is None or self._interp_y is None:
            return (0.0, 0.0)

        pt = np.array([[x, y]])
        off_x = float(self._interp_x(pt).flat[0])
        off_y = float(self._interp_y(pt).flat[0])
        return (off_x, off_y)

    def _ensure_interpolators(self, mesh: Mesh) -> None:
        current_hash = id(mesh)
        if self._interp_x is not None and self._mesh_hash == current_hash:
            return

        points = np.array([[p.x, p.y] for p in mesh])
        offsets_x = np.array([p.offset_x for p in mesh])
        offsets_y = np.array([p.offset_y for p in mesh])

        if len(points) < 4:  # pragma: no cover
            logger.warning("RBF interpolation needs at least 4 points")  # pragma: no cover
            self._interp_x = _ZeroInterpolator()  # pragma: no cover
            self._interp_y = _ZeroInterpolator()  # pragma: no cover
            self._mesh_hash = current_hash  # pragma: no cover
            return  # pragma: no cover

        kwargs = {}
        if self._epsilon is not None:
            kwargs["epsilon"] = self._epsilon
        elif self._kernel in {"multiquadric", "inverse_multiquadric", "gaussian"}:
            # Auto-compute epsilon as average nearest-neighbour distance
            from scipy.spatial.distance import pdist

            if len(points) > 1:
                kwargs["epsilon"] = float(np.median(pdist(points)))
            else:  # pragma: no cover
                kwargs["epsilon"] = 1.0  # pragma: no cover

        self._interp_x = RBFInterpolator(
            points,
            offsets_x,
            kernel=self._kernel,
            smoothing=self._smoothing,
            **kwargs,
        )
        self._interp_y = RBFInterpolator(
            points,
            offsets_y,
            kernel=self._kernel,
            smoothing=self._smoothing,
            **kwargs,
        )
        self._mesh_hash = current_hash
        logger.debug(
            "RBF interpolators rebuilt (kernel=%s, %d points)",
            self._kernel,
            len(points),
        )

    def name(self) -> str:
        """Return display name of the interpolation method."""
        return f"rbf_{self._kernel}"


class _ZeroInterpolator:
    """Fallback interpolator returning zero offsets."""

    def __call__(self, pt: np.ndarray) -> np.ndarray:  # pragma: no cover
        return np.zeros(pt.shape[0])  # pragma: no cover
