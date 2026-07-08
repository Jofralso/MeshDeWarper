"""Abstract base class for interpolation algorithms."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from mesh_de_warper.core.mesh import Mesh


class InterpolationAlgorithm(ABC):
    """Base class for all interpolation algorithms.

    Subclasses must implement ``interpolate()`` and ``name()``.
    Implementations must be stateless to allow caching and
    parallel evaluation.
    """

    @abstractmethod
    def interpolate(self, mesh: Mesh, x: float, y: float) -> tuple[float, float]:
        """Interpolate the distortion offset at nominal position (x, y).

        Args:
            mesh: The distortion mesh containing calibration points.
            x: Nominal X coordinate in mm.
            y: Nominal Y coordinate in mm.

        Returns:
            Tuple of (offset_x, offset_y) in mm.
        """

    @abstractmethod
    def name(self) -> str:
        """Return the canonical name of this algorithm."""
