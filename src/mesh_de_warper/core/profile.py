"""Calibration profile — serialisable snapshots of calibration state."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PROFILE_VERSION: int = 1


@dataclass
class CalibrationProfile:
    """A serialisable calibration profile.

    Stores the full calibration state for a specific printer configuration.

    Attributes:
        printer: Printer model name.
        bed_width: Bed width in mm.
        bed_height: Bed height in mm.
        spacing: Grid spacing in mm.
        interpolation: Name of the interpolation algorithm used.
        offsets: Mapping of (x, y) nominal coordinates to (offset_x, offset_y).
        firmware: Optional firmware identifier.
        version: Profile format version.
        created_at: ISO-8601 timestamp of creation.
        metadata: Optional metadata dictionary.
    """

    printer: str = ""
    bed_width: float = 220.0
    bed_height: float = 220.0
    spacing: float = 10.0
    interpolation: str = "bilinear"
    offsets: dict[tuple[float, float], tuple[float, float]] = field(default_factory=dict)
    firmware: str = ""
    version: int = PROFILE_VERSION
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Set creation timestamp if not provided."""
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialise profile to a JSON-compatible dictionary."""
        return {
            "version": self.version,
            "printer": self.printer,
            "bed_width": self.bed_width,
            "bed_height": self.bed_height,
            "spacing": self.spacing,
            "interpolation": self.interpolation,
            "firmware": self.firmware,
            "created_at": self.created_at,
            "metadata": self.metadata,
            "offsets": [
                {"x": kx, "y": ky, "offset_x": ox, "offset_y": oy}
                for (kx, ky), (ox, oy) in self.offsets.items()
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalibrationProfile:
        """Deserialise profile from a dictionary."""
        offsets = {
            (entry["x"], entry["y"]): (entry["offset_x"], entry["offset_y"])
            for entry in data.get("offsets", [])
        }
        return cls(
            printer=data.get("printer", ""),
            bed_width=data.get("bed_width", 220.0),
            bed_height=data.get("bed_height", 220.0),
            spacing=data.get("spacing", 10.0),
            interpolation=data.get("interpolation", "bilinear"),
            firmware=data.get("firmware", ""),
            version=data.get("version", PROFILE_VERSION),
            created_at=data.get("created_at", ""),
            metadata=data.get("metadata", {}),
            offsets=offsets,
        )

    def save(self, path: Path) -> None:
        """Save profile to a JSON file."""
        path = path.with_suffix(".json")
        path.write_text(json.dumps(self.to_dict(), indent=2))
        logger.info("Profile saved to %s", path)

    @classmethod
    def load(cls, path: Path) -> CalibrationProfile:
        """Load profile from a JSON file."""
        data = json.loads(path.read_text())
        return cls.from_dict(data)
