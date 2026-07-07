"""Tests for the visualization module."""

from __future__ import annotations

import dataclasses
import tempfile
from pathlib import Path

import numpy as np
import pytest

from cura_xy_calibration.core.mesh import Mesh
from cura_xy_calibration.visualization.heatmap import HeatmapConfig, HeatmapRenderer
from cura_xy_calibration.visualization.vector_field import VectorFieldConfig, VectorFieldRenderer
from cura_xy_calibration.visualization.preview import PreviewConfig, CalibrationPreview


@pytest.fixture
def uniform_mesh() -> Mesh:
    """A mesh with zero offsets (uniform, 5x5 grid, 200x200 mm)."""
    m = Mesh(200.0, 200.0, 50.0)
    m.reset_offsets()
    return m


@pytest.fixture
def distorted_mesh() -> Mesh:
    """A mesh with a synthetic radial distortion (5x5 grid, 200x200 mm)."""
    m = Mesh(200.0, 200.0, 50.0)
    m.reset_offsets()
    cx, cy = 100.0, 100.0
    k = 0.0001
    for r in range(m.rows):
        for c in range(m.cols):
            dx = m[r, c].x - cx
            dy = m[r, c].y - cy
            factor = k * (dx * dx + dy * dy)
            m[r, c] = dataclasses.replace(m[r, c], offset_x=dx * factor, offset_y=dy * factor)
    return m


@pytest.fixture
def tmp_output() -> Path:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = Path(f.name)
    yield path
    path.unlink(missing_ok=True)


class TestHeatmapRenderer:
    def test_render_zero_mesh(self, uniform_mesh: Mesh, tmp_output: Path) -> None:
        renderer = HeatmapRenderer()
        result = renderer.render(uniform_mesh, tmp_output)
        assert result == tmp_output.with_suffix(".png")
        assert result.exists()
        assert result.stat().st_size > 0

    def test_render_distorted_mesh(self, distorted_mesh: Mesh, tmp_output: Path) -> None:
        renderer = HeatmapRenderer()
        result = renderer.render(distorted_mesh, tmp_output)
        assert result.exists()
        assert result.stat().st_size > 0

    def test_custom_config(self, distorted_mesh: Mesh, tmp_output: Path) -> None:
        config = HeatmapConfig(colormap="plasma", dpi=72, title="Custom")
        renderer = HeatmapRenderer(config)
        result = renderer.render(distorted_mesh, tmp_output)
        assert result.exists()

    def test_invalid_colormap_fallback(self, distorted_mesh: Mesh, tmp_output: Path) -> None:
        config = HeatmapConfig(colormap="nonexistent")
        renderer = HeatmapRenderer(config)
        result = renderer.render(distorted_mesh, tmp_output)
        assert result.exists()

    def test_no_grid(self, distorted_mesh: Mesh, tmp_output: Path) -> None:
        config = HeatmapConfig(show_grid=False, show_colorbar=False)
        renderer = HeatmapRenderer(config)
        result = renderer.render(distorted_mesh, tmp_output)
        assert result.exists()

    def test_fixed_vrange(self, distorted_mesh: Mesh, tmp_output: Path) -> None:
        config = HeatmapConfig(vmin=0.0, vmax=5.0)
        renderer = HeatmapRenderer(config)
        result = renderer.render(distorted_mesh, tmp_output)
        assert result.exists()

    @pytest.mark.slow
    def test_high_resolution(self, distorted_mesh: Mesh, tmp_output: Path) -> None:
        renderer = HeatmapRenderer()
        result = renderer.render(distorted_mesh, tmp_output, resolution=400)
        assert result.exists()


class TestVectorFieldRenderer:
    def test_render_zero_mesh(self, uniform_mesh: Mesh, tmp_output: Path) -> None:
        renderer = VectorFieldRenderer()
        result = renderer.render(uniform_mesh, tmp_output)
        assert result.exists()
        # Zero mesh should produce "no offsets" message, but still write a file
        assert result.stat().st_size > 0

    def test_render_distorted_mesh(self, distorted_mesh: Mesh, tmp_output: Path) -> None:
        renderer = VectorFieldRenderer()
        result = renderer.render(distorted_mesh, tmp_output)
        assert result.exists()
        assert result.stat().st_size > 0

    def test_subsample(self, distorted_mesh: Mesh, tmp_output: Path) -> None:
        config = VectorFieldConfig(subsample=2)
        renderer = VectorFieldRenderer(config)
        result = renderer.render(distorted_mesh, tmp_output)
        assert result.exists()

    def test_custom_config(self, distorted_mesh: Mesh, tmp_output: Path) -> None:
        config = VectorFieldConfig(
            scale=2.0,
            width=0.005,
            color="#00ff00",
            alpha=0.5,
            dpi=72,
        )
        renderer = VectorFieldRenderer(config)
        result = renderer.render(distorted_mesh, tmp_output)
        assert result.exists()

    def test_single_arrow_mesh(self, tmp_output: Path) -> None:
        """A mesh with a single non-zero offset."""
        m = Mesh(100.0, 100.0, 50.0)
        m.reset_offsets()
        m[0, 0] = dataclasses.replace(m[0, 0], offset_x=5.0, offset_y=5.0)
        renderer = VectorFieldRenderer()
        result = renderer.render(m, tmp_output)
        assert result.exists()


class TestCalibrationPreview:
    def test_render_distorted(self, distorted_mesh: Mesh, tmp_output: Path) -> None:
        preview = CalibrationPreview()
        result = preview.render(distorted_mesh, tmp_output)
        assert result.exists()
        assert result.stat().st_size > 0

    def test_render_uniform(self, uniform_mesh: Mesh, tmp_output: Path) -> None:
        preview = CalibrationPreview()
        result = preview.render(uniform_mesh, tmp_output)
        assert result.exists()

    def test_custom_config(self, distorted_mesh: Mesh, tmp_output: Path) -> None:
        config = PreviewConfig(
            heatmap=HeatmapConfig(colormap="inferno"),
            vector_field=VectorFieldConfig(color="#ffffff"),
        )
        preview = CalibrationPreview(config)
        result = preview.render(distorted_mesh, tmp_output)
        assert result.exists()

    def test_small_mesh(self, tmp_output: Path) -> None:
        m = Mesh(50.0, 50.0, 25.0)
        m.reset_offsets()
        m[0, 0] = dataclasses.replace(m[0, 0], offset_x=2.0, offset_y=-2.0)
        preview = CalibrationPreview()
        result = preview.render(m, tmp_output)
        assert result.exists()


def test_import_all() -> None:
    """Verify all visualisation classes are importable from the package."""
    from cura_xy_calibration import HeatmapRenderer, VectorFieldRenderer, CalibrationPreview

    assert HeatmapRenderer is not None
    assert VectorFieldRenderer is not None
    assert CalibrationPreview is not None


@pytest.mark.slow
def test_all_renderers_produce_unique_output(distorted_mesh: Mesh, tmp_output: Path) -> None:
    """Each renderer should produce a different-looking image."""
    base = tmp_output.parent / "vis_test"
    base.mkdir(exist_ok=True)
    try:
        h = HeatmapRenderer().render(distorted_mesh, base / "heatmap.png")
        v = VectorFieldRenderer().render(distorted_mesh, base / "vector.png")
        p = CalibrationPreview().render(distorted_mesh, base / "preview.png")

        for f in (h, v, p):
            assert f.exists() and f.stat().st_size > 0

        # Files should differ in size (different visual output)
        sizes = {f.stat().st_size for f in (h, v, p)}
        assert len(sizes) >= 2
    finally:
        import shutil

        shutil.rmtree(base, ignore_errors=True)
