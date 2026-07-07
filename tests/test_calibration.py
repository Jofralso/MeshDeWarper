"""Tests for Calibration orchestrator."""

from __future__ import annotations

from cura_xy_calibration.core.calibration import Calibration
from cura_xy_calibration.core.mesh import Mesh
from cura_xy_calibration.interpolation.bilinear import BilinearInterpolation


class TestCalibration:
    def test_for_bed(self) -> None:
        cal = Calibration.for_bed(
            width=220.0,
            height=220.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        assert cal.mesh.rows == 23
        assert cal.mesh.cols == 23

    def test_correct_point_no_offset(self) -> None:
        cal = Calibration.for_bed(
            width=100.0,
            height=100.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        cx, cy = cal.correct_point(50.0, 50.0)
        assert cx == 50.0
        assert cy == 50.0

    def test_correct_point_with_offsets(self, calibration_with_offsets: Calibration) -> None:
        cx, cy = calibration_with_offsets.correct_point(50.0, 50.0)
        assert abs(cx - 50.5) < 0.01
        assert abs(cy - 49.7) < 0.01

    def test_offset_at(self) -> None:
        cal = Calibration.for_bed(
            width=100.0,
            height=100.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        ox, oy = cal.offset_at(50.0, 50.0)
        assert ox == 0.0
        assert oy == 0.0

    def test_residuals(self, calibration_with_offsets: Calibration) -> None:
        residuals = calibration_with_offsets.residuals()
        expected = (0.5**2 + 0.3**2) ** 0.5
        assert all(abs(r - expected) < 0.001 for r in residuals)

    def test_max_residual(self, calibration_with_offsets: Calibration) -> None:
        assert abs(calibration_with_offsets.max_residual() - (0.5**2 + 0.3**2) ** 0.5) < 0.001

    def test_mean_residual(self, calibration_with_offsets: Calibration) -> None:
        mean = calibration_with_offsets.mean_residual()
        expected = (0.5**2 + 0.3**2) ** 0.5
        assert abs(mean - expected) < 0.001

    def test_empty_residuals(self) -> None:
        mesh = Mesh(width=0, height=0, spacing=10)
        cal = Calibration(mesh=mesh, interpolation=BilinearInterpolation())
        assert cal.max_residual() == 0.0
        assert cal.mean_residual() == 0.0

    def test_from_to_profile(self, calibration_with_offsets: Calibration) -> None:
        profile = calibration_with_offsets.to_profile()
        assert profile.interpolation == "bilinear"
        assert profile.bed_width == 100.0

        restored = Calibration.from_profile(profile, BilinearInterpolation())
        assert restored.mesh.rows == calibration_with_offsets.mesh.rows
        assert restored.mesh.cols == calibration_with_offsets.mesh.cols

        # Check offsets preserved
        for p_orig, p_rest in zip(calibration_with_offsets.mesh, restored.mesh):
            assert abs(p_orig.offset_x - p_rest.offset_x) < 0.001
            assert abs(p_orig.offset_y - p_rest.offset_y) < 0.001
