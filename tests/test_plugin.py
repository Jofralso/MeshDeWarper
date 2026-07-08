"""Tests for Cura plugin entry point."""

from __future__ import annotations

from pathlib import Path

import pytest

from mesh_de_warper.core.calibration import Calibration
from mesh_de_warper.interpolation.bilinear import BilinearInterpolation
from mesh_de_warper.plugin import CuraPlugin, get_meta_data, register


class TestCuraPlugin:
    def test_initial_state(self) -> None:
        plugin = CuraPlugin()
        assert plugin.enabled
        assert plugin.get_calibration() is None

    def test_enable_disable(self) -> None:
        plugin = CuraPlugin()
        assert plugin.enabled
        plugin.set_enabled(False)
        assert not plugin.enabled
        plugin.set_enabled(True)
        assert plugin.enabled

    def test_set_calibration(self) -> None:
        plugin = CuraPlugin()
        cal = Calibration.for_bed(
            width=100.0,
            height=100.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        plugin.set_calibration(cal)
        assert plugin.get_calibration() is not None
        assert plugin.get_calibration().mesh.num_points == cal.mesh.num_points

    def test_save_load_profile(self, temp_dir: Path) -> None:
        plugin = CuraPlugin()
        cal = Calibration.for_bed(
            width=100.0,
            height=100.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        plugin.set_calibration(cal)

        path = temp_dir / "test_profile.json"
        plugin.save_profile(path)

        plugin2 = CuraPlugin()
        plugin2.load_profile(path)
        assert plugin2.get_calibration() is not None
        assert plugin2.get_calibration().mesh.num_points == 121

    def test_save_without_calibration_raises(self) -> None:
        plugin = CuraPlugin()
        with pytest.raises(RuntimeError, match="No calibration to save"):
            plugin.save_profile(Path("/tmp/test.json"))  # noqa: S108

    def test_warp_without_calibration_raises(self) -> None:
        plugin = CuraPlugin()
        with pytest.raises(RuntimeError, match="No calibration loaded"):
            plugin.warp_gcode(Path("/tmp/in.gcode"), Path("/tmp/out.gcode"))  # noqa: S108

    def test_reset_calibration_without_calibration(self) -> None:
        plugin = CuraPlugin()
        plugin.reset_calibration()

    def test_reset_calibration(self) -> None:
        plugin = CuraPlugin()
        cal = Calibration.for_bed(
            width=100.0,
            height=100.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        cal.mesh[0, 0] = cal.mesh[0, 0].with_offset(1.0, 2.0)
        plugin.set_calibration(cal)
        plugin.reset_calibration()
        assert plugin.get_calibration().mesh[0, 0].offset_x == 0.0

    def test_register(self) -> None:
        plugin = register()
        assert isinstance(plugin, CuraPlugin)

    def test_get_meta_data(self) -> None:
        meta = get_meta_data()
        assert "version" in meta
        assert "plugin_name" in meta
        assert meta["plugin_name"] == "XY Distortion Calibration"

    def test_interpolation_from_name(self) -> None:
        plugin = CuraPlugin()
        interp = plugin._interpolation_from_name("bilinear")
        assert interp.name() == "bilinear"

    def test_interpolation_from_unknown_name(self) -> None:
        plugin = CuraPlugin()
        interp = plugin._interpolation_from_name("nonexistent")
        assert interp.name() == "bilinear"  # fallback

    def test_warp_with_calibration(self, temp_dir: Path) -> None:
        plugin = CuraPlugin()
        cal = Calibration.for_bed(
            width=100.0,
            height=100.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        plugin.set_calibration(cal)
        input_path = temp_dir / "input.gcode"
        output_path = temp_dir / "output.gcode"
        input_path.write_text("G1 X10 Y20\nG1 X30 Y40\n")
        plugin.warp_gcode(input_path, output_path)
        assert output_path.exists()
        content = output_path.read_text()
        assert "G1" in content

    def test_warp_disabled_copies_input_to_output(self, temp_dir: Path) -> None:
        plugin = CuraPlugin()
        plugin.set_enabled(False)
        input_path = temp_dir / "input.gcode"
        output_path = temp_dir / "output.gcode"
        input_path.write_text("G1 X10 Y20\n")
        plugin.warp_gcode(input_path, output_path)
        assert output_path.exists()
        assert output_path.read_text() == "G1 X10 Y20\n"
