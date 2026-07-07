"""Vision-assisted calibration assistant."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from cura_xy_calibration.core.calibration import Calibration
from cura_xy_calibration.core.point import Point
from cura_xy_calibration.interpolation.bilinear import BilinearInterpolation
from cura_xy_calibration.vision.correction import LensCorrector, PerspectiveCorrector
from cura_xy_calibration.vision.detection import PointDetector

logger = logging.getLogger(__name__)


@dataclass
class CandidateCalibration:
    """A calibration produced by the vision assistant for user review.

    Attributes:
        calibration: The proposed calibration.
        confidence: Per-point confidence scores.
        low_confidence_points: Indices of points below confidence threshold.
        source_image: Path to the source image.
    """

    calibration: Calibration
    confidence: list[float]
    low_confidence_points: list[int]
    source_image: str = ""


class VisionCalibrationAssistant:
    """Experimental vision assistant for automated calibration.

    Workflow:
        1. Load image
        2. Apply lens correction
        3. Apply perspective correction
        4. Detect printed points
        5. Estimate offsets vs expected grid
        6. Return candidate calibration for user validation

    The assistant NEVER automatically modifies the calibration profile.
    All results require user validation before merging.
    """

    def __init__(
        self,
        point_detector: PointDetector | None = None,
        lens_corrector: LensCorrector | None = None,
        perspective_corrector: PerspectiveCorrector | None = None,
        confidence_threshold: float = 0.7,
    ) -> None:
        self._point_detector = point_detector or PointDetector()
        self._lens_corrector = lens_corrector or LensCorrector()
        self._perspective_corrector = perspective_corrector or PerspectiveCorrector()
        self._confidence_threshold = confidence_threshold

    def process_image(
        self,
        image_path: Path,
        bed_width: float,
        bed_height: float,
        spacing: float,
    ) -> CandidateCalibration:
        """Process a calibration pattern image and produce a candidate calibration.

        Args:
            image_path: Path to the image file.
            bed_width: Bed width in mm.
            bed_height: Bed height in mm.
            spacing: Grid spacing in mm.

        Returns:
            A CandidateCalibration for user review.
        """
        try:
            import cv2
        except ImportError:
            msg = "OpenCV is required for vision-assisted calibration"
            raise ImportError(msg) from None

        img = cv2.imread(str(image_path))
        if img is None:
            msg = f"Cannot load image: {image_path}"
            raise FileNotFoundError(msg)

        # Apply corrections
        img = self._lens_corrector.correct(img)
        img = self._perspective_corrector.correct(img)

        # Detect points
        detection = self._point_detector.detect(image_path)

        if not detection.detected_points:
            msg = "No points detected in the image"
            raise RuntimeError(msg)

        # Build expected grid
        cols = int(bed_width / spacing) + 1
        rows = int(bed_height / spacing) + 1
        expected_count = cols * rows

        detected = detection.detected_points
        confidences = detection.confidence

        if len(detected) != expected_count:
            logger.warning(
                "Detected %d points but expected %d (%dx%d grid)",
                len(detected),
                expected_count,
                cols,
                rows,
            )

        # Find low-confidence points
        low_conf = [i for i, c in enumerate(confidences) if c < self._confidence_threshold]
        if low_conf:
            logger.warning(
                "Low confidence for points: %s",
                ", ".join(str(i) for i in low_conf),
            )

        # Estimate offsets by comparing detected positions to nominal grid
        calibration = Calibration.for_bed(
            width=bed_width,
            height=bed_height,
            spacing=spacing,
            interpolation=BilinearInterpolation(),
        )

        for i, (dx, dy) in enumerate(detected):
            if i >= calibration.mesh.num_points:
                break
            row = i // cols
            col = i % cols
            if row < calibration.mesh.rows and col < calibration.mesh.cols:
                nominal = calibration.mesh[row, col]
                offset_x = dx - nominal.x
                offset_y = dy - nominal.y
                calibration.mesh[row, col] = Point(
                    x=nominal.x,
                    y=nominal.y,
                    offset_x=offset_x,
                    offset_y=offset_y,
                )

        return CandidateCalibration(
            calibration=calibration,
            confidence=confidences,
            low_confidence_points=low_conf,
            source_image=str(image_path),
        )
