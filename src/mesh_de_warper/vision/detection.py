"""Point detection from calibration pattern images."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Result of point detection on a calibration pattern image.

    Attributes:
        detected_points: List of (x, y) detected positions in mm.
        confidence: Per-point confidence score (0..1).
        grid_cols: Number of detected columns.
        grid_rows: Number of detected rows.
        image_path: Path to the source image.
    """

    detected_points: list[tuple[float, float]] = field(default_factory=list)
    confidence: list[float] = field(default_factory=list)
    grid_cols: int = 0
    grid_rows: int = 0
    image_path: str = ""


class PointDetector:
    """Detects calibration points in an image of the calibration pattern.

    Uses computer vision techniques to locate printed points and
    estimate their positions relative to the expected grid.
    """

    def __init__(
        self,
        blur_ksize: int = 5,
        block_size: int = 51,
        c_value: float = 10.0,
        min_radius: int = 3,
        max_radius: int = 20,
    ) -> None:
        self._blur_ksize = blur_ksize
        self._block_size = block_size
        self._c_value = c_value
        self._min_radius = min_radius
        self._max_radius = max_radius

    def detect(self, image_path: Path) -> DetectionResult:
        """Detect calibration points in an image."""
        try:
            import cv2
        except ImportError:  # pragma: no cover
            logger.error("OpenCV not available; install with: pip install opencv-python-headless")
            return DetectionResult(image_path=str(image_path))

        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            logger.error("Failed to load image: %s", image_path)
            return DetectionResult(image_path=str(image_path))

        # Preprocessing
        blurred = cv2.GaussianBlur(img, (self._blur_ksize, self._blur_ksize), 0)
        binary = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            self._block_size,
            self._c_value,
        )

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        points: list[tuple[float, float]] = []
        confidence: list[float] = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 10:
                continue

            ((cx, cy), radius) = cv2.minEnclosingCircle(cnt)
            if radius < self._min_radius or radius > self._max_radius:
                continue

            # Confidence based on circularity
            perimeter = cv2.arcLength(cnt, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            circ_conf = min(1.0, max(0.0, circularity))

            # Confidence based on area consistency
            area_conf = min(1.0, area / (np.pi * (self._max_radius**2)))

            points.append((float(cx), float(cy)))
            confidence.append(float((circ_conf + area_conf) / 2))

        logger.info(
            "Detected %d points in %s (%.1f%% high confidence)",
            len(points),
            image_path,
            sum(1 for c in confidence if c > 0.7) / max(len(confidence), 1) * 100,
        )

        return DetectionResult(
            detected_points=points,
            confidence=confidence,
            grid_cols=0,
            grid_rows=0,
            image_path=str(image_path),
        )
