"""Shared test fixtures."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from mesh_de_warper.core.calibration import Calibration
from mesh_de_warper.core.mesh import Mesh
from mesh_de_warper.core.point import Point
from mesh_de_warper.core.profile import CalibrationProfile
from mesh_de_warper.interpolation.bilinear import BilinearInterpolation


@pytest.fixture
def sample_mesh() -> Mesh:
    return Mesh(width=100.0, height=100.0, spacing=10.0)


@pytest.fixture
def calibration() -> Calibration:
    return Calibration.for_bed(
        width=100.0,
        height=100.0,
        spacing=10.0,
        interpolation=BilinearInterpolation(),
    )


@pytest.fixture
def calibration_with_offsets() -> Calibration:
    cal = Calibration.for_bed(
        width=100.0,
        height=100.0,
        spacing=10.0,
        interpolation=BilinearInterpolation(),
    )
    for row in range(cal.mesh.rows):
        for col in range(cal.mesh.cols):
            cal.mesh[row, col] = Point(
                x=cal.mesh[row, col].x,
                y=cal.mesh[row, col].y,
                offset_x=0.5,
                offset_y=-0.3,
            )
    return cal


@pytest.fixture
def sample_profile() -> CalibrationProfile:
    return CalibrationProfile(
        printer="TestPrinter",
        bed_width=220.0,
        bed_height=220.0,
        spacing=10.0,
        interpolation="bilinear",
        offsets={
            (0.0, 0.0): (0.1, 0.2),
            (10.0, 0.0): (0.3, 0.4),
            (0.0, 10.0): (0.5, 0.6),
            (10.0, 10.0): (0.7, 0.8),
        },
    )


@pytest.fixture
def temp_dir(tmp_path: Path) -> Generator[Path, None, None]:
    yield tmp_path
