"""Tests for G-code warping engine."""

from __future__ import annotations

from pathlib import Path

from cura_xy_calibration.core.calibration import Calibration
from cura_xy_calibration.core.point import Point
from cura_xy_calibration.gcode.warper import GCodeWarper
from cura_xy_calibration.interpolation.bilinear import BilinearInterpolation


class TestGCodeWarper:
    def test_warp_simple_move(self) -> None:
        cal = Calibration.for_bed(
            width=100.0,
            height=100.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        # Add some offset
        cal.mesh[5, 5] = Point(x=50.0, y=50.0, offset_x=1.0, offset_y=1.0)

        warper = GCodeWarper(cal)
        gcode = "G1 X50 Y50"
        ast = warper.warp(gcode)
        cmd = ast.all_commands()[0]
        pos = cmd.position
        assert pos.x is not None
        assert pos.y is not None
        assert abs(pos.x - 51.0) < 0.01
        assert abs(pos.y - 51.0) < 0.01

    def test_warp_no_offset(self) -> None:
        cal = Calibration.for_bed(
            width=100.0,
            height=100.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        warper = GCodeWarper(cal)
        gcode = "G1 X10 Y10"
        ast = warper.warp(gcode)
        cmd = ast.all_commands()[0]
        assert cmd.position.x == 10.0
        assert cmd.position.y == 10.0

    def test_rapid_move_warped(self) -> None:
        cal = Calibration.for_bed(
            width=100.0,
            height=100.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        cal.mesh[5, 5] = Point(x=50.0, y=50.0, offset_x=1.0, offset_y=0.0)
        warper = GCodeWarper(cal)
        gcode = "G0 X50 Y50"
        ast = warper.warp(gcode)
        cmd = ast.all_commands()[0]
        assert cmd.g_code == 0

    def test_warp_file(self, temp_dir: Path) -> None:
        cal = Calibration.for_bed(
            width=100.0,
            height=100.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        cal.mesh[5, 5] = Point(x=50.0, y=50.0, offset_x=1.0, offset_y=1.0)

        input_path = temp_dir / "input.gcode"
        output_path = temp_dir / "output.gcode"
        input_path.write_text("G1 X50 Y50\nG1 X60 Y60")

        warper = GCodeWarper(cal)
        warper.warp_file(input_path, output_path)
        assert output_path.exists()
        content = output_path.read_text()
        assert "G1" in content
        assert "X51" in content or "X50.9999" in content

    def test_absolute_mode_preserved(self) -> None:
        cal = Calibration.for_bed(
            width=100.0,
            height=100.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        cal.mesh[5, 5] = Point(x=50.0, y=50.0, offset_x=2.0, offset_y=0.0)
        warper = GCodeWarper(cal)
        gcode = "G90\nG1 X50 Y50"
        ast = warper.warp(gcode)
        assert ast.all_commands()[0].g_code == 90

    def test_non_move_command_preserved(self) -> None:
        cal = Calibration.for_bed(
            width=100.0,
            height=100.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        warper = GCodeWarper(cal)
        gcode = "M104 S200"
        ast = warper.warp(gcode)
        cmd = ast.all_commands()[0]
        assert cmd.m_code == 104
        assert cmd.words[0].value == 104

    def test_extrusion_preserved(self) -> None:
        cal = Calibration.for_bed(
            width=100.0,
            height=100.0,
            spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        warper = GCodeWarper(cal)
        gcode = "G1 X50 Y50 E1.5"
        ast = warper.warp(gcode)
        cmd = ast.all_commands()[0]
        assert cmd.position.e == 1.5
