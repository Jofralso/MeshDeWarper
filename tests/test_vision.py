"""Tests for experimental vision module."""

from __future__ import annotations

from pathlib import Path

import pytest

from mesh_de_warper.vision.calibration import VisionCalibrationAssistant
from mesh_de_warper.vision.correction import LensCorrector, PerspectiveCorrector
from mesh_de_warper.vision.detection import DetectionResult, PointDetector


class TestDetectionResult:
    def test_default_creation(self) -> None:
        result = DetectionResult()
        assert result.detected_points == []
        assert result.confidence == []
        assert result.grid_cols == 0

    def test_with_data(self) -> None:
        result = DetectionResult(
            detected_points=[(10.0, 20.0), (30.0, 40.0)],
            confidence=[0.9, 0.8],
            grid_cols=2,
            grid_rows=1,
            image_path="/tmp/test.png",  # noqa: S108
        )
        assert len(result.detected_points) == 2
        assert result.confidence[0] == 0.9


class TestPointDetector:
    def test_detect_no_opencv(self) -> None:
        detector = PointDetector()
        result = detector.detect(Path("/nonexistent/image.png"))
        assert isinstance(result, DetectionResult)
        assert result.detected_points == []


class TestLensCorrector:
    def test_correct_without_calibration(self) -> None:
        import numpy as np

        corrector = LensCorrector()
        img = np.zeros((100, 100), dtype=np.uint8)
        result = corrector.correct(img)
        assert result is img  # returns original

    def test_set_calibration(self) -> None:
        import numpy as np

        corrector = LensCorrector()
        camera = np.eye(3)
        dist = np.zeros(5)
        corrector.set_calibration(camera, dist)
        img = np.zeros((100, 100), dtype=np.uint8)
        result = corrector.correct(img)
        assert result is not None


class TestPerspectiveCorrector:
    def test_correct_without_corners(self) -> None:
        import numpy as np

        corrector = PerspectiveCorrector()
        img = np.zeros((100, 100), dtype=np.uint8)
        result = corrector.correct(img)
        assert result is img

    def test_set_corners_valid(self) -> None:
        corrector = PerspectiveCorrector()
        src = [(0, 0), (100, 0), (100, 100), (0, 100)]
        dst = [(10, 10), (90, 10), (90, 90), (10, 90)]
        corrector.set_corners(src, dst)

    def test_set_corners_invalid(self) -> None:
        corrector = PerspectiveCorrector()
        with pytest.raises(ValueError, match="4 corner"):
            corrector.set_corners([(0, 0)], [(10, 10)])


class TestVisionCalibrationAssistant:
    def test_process_nonexistent_image(self) -> None:
        assistant = VisionCalibrationAssistant()
        with pytest.raises(FileNotFoundError):
            assistant.process_image(
                Path("/nonexistent/image.png"),
                bed_width=100.0,
                bed_height=100.0,
                spacing=10.0,
            )

    def test_create_assistant(self) -> None:
        assistant = VisionCalibrationAssistant(confidence_threshold=0.5)
        assert assistant is not None
