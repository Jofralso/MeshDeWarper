"""Tests for pattern generators."""

from __future__ import annotations

from pathlib import Path

from mesh_de_warper.patterns.base import (
    FiducialMarker,
    PatternConfig,
    PointStyle,
)
from mesh_de_warper.patterns.pdf_generator import PdfPatternGenerator
from mesh_de_warper.patterns.stl_generator import StlPatternGenerator
from mesh_de_warper.patterns.svg_generator import SvgPatternGenerator


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


class TestSvgPatternGeneratorEdgeCases:
    def test_generate_with_fiducials(self, temp_dir: Path) -> None:
        from mesh_de_warper.patterns.base import FiducialMarker
        for fid in FiducialMarker:
            config = PatternConfig(
                bed_width=30.0, bed_height=30.0, spacing=10.0,
                fiducial=fid,
            )
            gen = SvgPatternGenerator()
            path = gen.generate(config, temp_dir / f"test_fid_{fid.name}")
            assert path.exists()
            content = path.read_text()
            assert "<svg" in content

    def test_generate_with_point_styles(self, temp_dir: Path) -> None:
        from mesh_de_warper.patterns.base import PointStyle
        for style in PointStyle:
            config = PatternConfig(
                bed_width=30.0, bed_height=30.0, spacing=10.0,
                point_style=style,
            )
            gen = SvgPatternGenerator()
            path = gen.generate(config, temp_dir / f"test_ps_{style.name}")
            assert path.exists()
            assert path.read_text()

    def test_generate_no_fiducial_none(self, temp_dir: Path) -> None:
        config = PatternConfig(
            bed_width=30.0, bed_height=30.0, spacing=10.0,
        )
        config.fiducial = None  # type: ignore[assignment]
        gen = SvgPatternGenerator()
        path = gen.generate(config, temp_dir / "test_no_fid")
        assert path.exists()


class TestStlPatternGenerator:
    def test_generate_stl(self, temp_dir: Path) -> None:
        config = PatternConfig(
            bed_width=50.0,
            bed_height=50.0,
            spacing=10.0,
        )
        gen = StlPatternGenerator()
        path = gen.generate(config, temp_dir / "test_pattern")
        assert path.exists()
        assert path.suffix == ".stl"
        assert path.stat().st_size > 100

    def test_generated_stl_has_geometry(self, temp_dir: Path) -> None:
        config = PatternConfig(
            bed_width=30.0,
            bed_height=30.0,
            spacing=10.0,
        )
        gen = StlPatternGenerator()
        path = gen.generate(config, temp_dir / "test_geom")
        from stl import mesh as stl_mesh
        loaded = stl_mesh.Mesh.from_file(str(path))
        assert len(loaded.vectors) > 0
        # Should have at least substrate (12 faces) + features
        assert loaded.vectors.shape[0] >= 12

    def test_generate_with_different_sizes(self, temp_dir: Path) -> None:
        config = PatternConfig(
            bed_width=60.0,
            bed_height=40.0,
            spacing=20.0,
        )
        gen = StlPatternGenerator(substrate_height=0.5, feature_height=1.0)
        path = gen.generate(config, temp_dir / "test_sizes")
        assert path.exists()
        assert path.stat().st_size > 0
