"""Tests for vision detection and correction with real image processing."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from mesh_de_warper.vision.calibration import VisionCalibrationAssistant
from mesh_de_warper.vision.correction import LensCorrector, PerspectiveCorrector
from mesh_de_warper.vision.detection import PointDetector


class TestPointDetectorReal:
    def test_detect_with_synthetic_image(self, temp_dir: Path) -> None:
        import cv2

        img = np.ones((500, 500), dtype=np.uint8) * 255
        # Draw dark circles as calibration points
        for cx, cy in [(100, 100), (200, 100), (100, 200), (200, 200)]:
            cv2.circle(img, (cx, cy), 8, 0, -1)

        img_path = temp_dir / "test_grid.png"
        cv2.imwrite(str(img_path), img)

        detector = PointDetector(min_radius=3, max_radius=20)
        result = detector.detect(img_path)
        assert len(result.detected_points) >= 3  # should find most points
        assert len(result.confidence) == len(result.detected_points)
        assert result.image_path == str(img_path)

    def test_detect_without_points(self, temp_dir: Path) -> None:
        img = np.ones((100, 100), dtype=np.uint8) * 255
        img_path = temp_dir / "blank.png"
        import cv2
        cv2.imwrite(str(img_path), img)

        detector = PointDetector()
        result = detector.detect(img_path)
        assert len(result.detected_points) == 0

    def test_detect_noisy_image(self, temp_dir: Path) -> None:
        import cv2

        rng = np.random.default_rng(42)
        img = rng.integers(0, 255, (200, 200), dtype=np.uint8)
        img_path = temp_dir / "noisy.png"
        cv2.imwrite(str(img_path), img)

        detector = PointDetector(blur_ksize=7, block_size=51, c_value=20)
        result = detector.detect(img_path)
        from mesh_de_warper.vision.detection import DetectionResult
        assert isinstance(result, DetectionResult)


class TestLensCorrectorReal:
    def test_lens_correct_distorted(self) -> None:
        corrector = LensCorrector()
        camera = np.array([[500, 0, 320], [0, 500, 240], [0, 0, 1]], dtype=np.float64)
        dist = np.array([0.1, -0.05, 0.001, 0.001, 0.01], dtype=np.float64)
        corrector.set_calibration(camera, dist)
        img = np.zeros((480, 640), dtype=np.uint8)
        result = corrector.correct(img)
        assert result is not None
        assert result.shape == img.shape[:2] or result.size > 0

    def test_lens_correct_without_calibration(self) -> None:
        corrector = LensCorrector()
        img = np.zeros((100, 100), dtype=np.uint8)
        result = corrector.correct(img)
        assert result is img


class TestPerspectiveCorrectorReal:
    def test_perspective_correct(self, temp_dir: Path) -> None:
        import cv2

        img = np.zeros((200, 200), dtype=np.uint8)
        img[50:150, 50:150] = 200  # white square
        img_path = temp_dir / "perspective_test.png"
        cv2.imwrite(str(img_path), img)

        corrector = PerspectiveCorrector()
        src = [(50, 50), (150, 50), (150, 150), (50, 150)]
        dst = [(0, 0), (200, 0), (200, 200), (0, 200)]
        corrector.set_corners(src, dst)
        result = corrector.correct(img)
        assert result is not None
        assert result.shape == img.shape

    def test_perspective_without_corners(self) -> None:
        corrector = PerspectiveCorrector()
        img = np.zeros((100, 100), dtype=np.uint8)
        result = corrector.correct(img)
        assert result is img


class TestVisionAssistantReal:
    def test_process_synthetic_image(self, temp_dir: Path) -> None:
        import cv2

        img = np.ones((500, 500), dtype=np.uint8) * 255
        # Draw a grid of dark circles
        spacing_px = 100
        for row in range(3):
            for col in range(3):
                cx = 50 + col * spacing_px
                cy = 50 + row * spacing_px
                cv2.circle(img, (cx, cy), 8, 0, -1)

        img_path = temp_dir / "vision_assist.png"
        cv2.imwrite(str(img_path), img)

        assistant = VisionCalibrationAssistant(confidence_threshold=0.3)
        result = assistant.process_image(
            img_path,
            bed_width=200.0,
            bed_height=200.0,
            spacing=100.0,
        )
        assert result.calibration is not None
        assert result.source_image == str(img_path)

    def test_process_empty_image_raises(self, temp_dir: Path) -> None:
        img = np.ones((100, 100), dtype=np.uint8) * 255
        img_path = temp_dir / "empty.png"
        import cv2
        cv2.imwrite(str(img_path), img)

        assistant = VisionCalibrationAssistant()
        with pytest.raises(RuntimeError, match="No points detected"):
            assistant.process_image(
                img_path,
                bed_width=200.0,
                bed_height=200.0,
                spacing=100.0,
            )

    def test_process_mismatched_count(self, temp_dir: Path) -> None:
        import cv2
        # 2x2 grid = 4 points, but bed expects 3x3 = 9
        img = np.ones((300, 300), dtype=np.uint8) * 255
        for cx, cy in [(50, 50), (150, 50), (50, 150), (150, 150)]:
            cv2.circle(img, (cx, cy), 8, 0, -1)
        img_path = temp_dir / "mismatch.png"
        cv2.imwrite(str(img_path), img)

        assistant = VisionCalibrationAssistant(confidence_threshold=0.7)
        result = assistant.process_image(
            img_path,
            bed_width=200.0,
            bed_height=200.0,
            spacing=100.0,
        )
        assert len(result.confidence) == 4

    def test_process_more_points_than_mesh(self, temp_dir: Path) -> None:
        import cv2
        # Many points, but very small bed → mesh has only 2x2=4 points
        img = np.ones((300, 300), dtype=np.uint8) * 255
        for row in range(3):
            for col in range(3):
                cv2.circle(img, (50 + col * 100, 50 + row * 100), 6, 0, -1)
        img_path = temp_dir / "oversized.png"
        cv2.imwrite(str(img_path), img)

        assistant = VisionCalibrationAssistant(confidence_threshold=0.3)
        result = assistant.process_image(
            img_path,
            bed_width=10.0,
            bed_height=10.0,
            spacing=100.0,
        )
        assert result.calibration is not None
