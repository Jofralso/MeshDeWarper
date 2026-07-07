"""Abstract base class for pattern generators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


class PointStyle(Enum):
    """Visual style for calibration points."""

    CROSS = auto()
    DOT = auto()
    CIRCLE = auto()
    TARGET = auto()


class FiducialMarker(Enum):
    """Type of fiducial marker."""

    CORNER_CROSS = auto()
    CORNER_CIRCLE = auto()
    CORNER_TARGET = auto()
    NONE = auto()


@dataclass
class PatternConfig:
    """Configuration for calibration pattern generation.

    Attributes:
        bed_width: Bed width in mm.
        bed_height: Bed height in mm.
        spacing: Grid spacing in mm.
        point_style: Visual style for points.
        point_size: Size of points in mm.
        show_numbers: Whether to number each point.
        number_font_size: Font size for numbering in mm.
        fiducial: Type of fiducial marker.
        fiducial_size: Size of fiducial marker in mm.
        margin: Margin around the grid in mm.
    """

    bed_width: float = 220.0
    bed_height: float = 220.0
    spacing: float = 10.0
    point_style: PointStyle = PointStyle.CROSS
    point_size: float = 2.0
    show_numbers: bool = True
    number_font_size: float = 2.5
    fiducial: FiducialMarker = FiducialMarker.CORNER_CROSS
    fiducial_size: float = 8.0
    margin: float = 5.0
    metadata: dict[str, str] = field(default_factory=dict)


class PatternGenerator(ABC):
    """Abstract base for calibration pattern generators."""

    @abstractmethod
    def generate(self, config: PatternConfig, output_path: Path) -> Path:
        """Generate a calibration pattern and write to output_path."""
