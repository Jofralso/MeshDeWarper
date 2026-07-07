"""Tests for pattern generators."""

from __future__ import annotations

from pathlib import Path

from cura_xy_calibration.patterns.base import (
    FiducialMarker,
    PatternConfig,
    PointStyle,
)
from cura_xy_calibration.patterns.pdf_generator import PdfPatternGenerator
from cura_xy_calibration.patterns.svg_generator import SvgPatternGenerator


class TestPatternConfig:
    def test_defaults(self) -> None:
        config = PatternConfig()
        assert config.bed_width == 220.0
        assert config.spacing == 10.0
        assert config.point_style == PointStyle.CROSS
        assert config.fiducial == FiducialMarker.CORNER_CROSS
        assert config.show_numbers


class TestPdfPatternGenerator:
    def test_generate_pdf(self, temp_dir: Path) -> None:
        config = PatternConfig(
            bed_width=50.0,
            bed_height=50.0,
            spacing=10.0,
        )
        gen = PdfPatternGenerator()
        path = gen.generate(config, temp_dir / "test_pattern")
        assert path.exists()
        assert path.suffix == ".pdf"
        assert path.stat().st_size > 100

    def test_generate_with_different_styles(self, temp_dir: Path) -> None:
        for style in PointStyle:
            config = PatternConfig(
                bed_width=30.0,
                bed_height=30.0,
                spacing=10.0,
                point_style=style,
            )
            gen = PdfPatternGenerator()
            path = gen.generate(config, temp_dir / f"test_{style.name}")
            assert path.exists()


class TestSvgPatternGenerator:
    def test_generate_svg(self, temp_dir: Path) -> None:
        config = PatternConfig(
            bed_width=50.0,
            bed_height=50.0,
            spacing=10.0,
        )
        gen = SvgPatternGenerator()
        path = gen.generate(config, temp_dir / "test_pattern")
        assert path.exists()
        assert path.suffix == ".svg"
        content = path.read_text()
        assert "<svg" in content
        assert "xmlns" in content

    def test_generate_no_numbers(self, temp_dir: Path) -> None:
        config = PatternConfig(
            bed_width=30.0,
            bed_height=30.0,
            spacing=10.0,
            show_numbers=False,
        )
        gen = SvgPatternGenerator()
        path = gen.generate(config, temp_dir / "test_nonum")
        assert path.exists()
