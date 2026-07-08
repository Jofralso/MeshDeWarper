"""Lens and perspective correction for calibration images."""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


class LensCorrector:
    """Applies lens distortion correction to calibration images.

    Uses OpenCV camera calibration parameters to undistort images
    before point detection.
    """

    def __init__(self) -> None:
        self._camera_matrix: np.ndarray | None = None
        self._dist_coeffs: np.ndarray | None = None

    def set_calibration(
        self,
        camera_matrix: np.ndarray,
        dist_coeffs: np.ndarray,
    ) -> None:
        """Set camera intrinsics and distortion coefficients."""
        self._camera_matrix = camera_matrix
        self._dist_coeffs = dist_coeffs

    def correct(self, image: np.ndarray) -> np.ndarray:
        """Apply lens distortion correction to an image."""
        if self._camera_matrix is None or self._dist_coeffs is None:
            logger.warning("No camera calibration set; returning original image")
            return image

        try:
            import cv2

            h, w = image.shape[:2]
            new_camera, roi = cv2.getOptimalNewCameraMatrix(
                self._camera_matrix,
                self._dist_coeffs,
                (w, h),
                1,
                (w, h),
            )
            corrected = cv2.undistort(
                image, self._camera_matrix, self._dist_coeffs, None, new_camera
            )
            x, y, w_, h_ = roi
            return corrected[y : y + h_, x : x + w_]
        except ImportError:  # pragma: no cover
            logger.error("OpenCV not available for lens correction")
            return image


class PerspectiveCorrector:
    """Corrects perspective distortion from angled camera shots."""

    def __init__(self) -> None:
        self._src_points: np.ndarray | None = None
        self._dst_points: np.ndarray | None = None

    def set_corners(
        self,
        src_corners: list[tuple[float, float]],
        dst_corners: list[tuple[float, float]],
    ) -> None:
        """Set source and destination corner points for perspective transform."""
        if len(src_corners) != 4 or len(dst_corners) != 4:
            msg = "Must provide exactly 4 corner points"
            raise ValueError(msg)
        self._src_points = np.array(src_corners, dtype=np.float32)
        self._dst_points = np.array(dst_corners, dtype=np.float32)

    def correct(self, image: np.ndarray) -> np.ndarray:
        """Apply perspective correction to an image."""
        if self._src_points is None or self._dst_points is None:
            logger.warning("No corner points set; returning original image")
            return image

        try:
            import cv2

            matrix = cv2.getPerspectiveTransform(self._src_points, self._dst_points)
            h, w = image.shape[:2]
            return cv2.warpPerspective(image, matrix, (w, h))
        except ImportError:  # pragma: no cover
            logger.error("OpenCV not available for perspective correction")
            return image
