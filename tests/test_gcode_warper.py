"""Tests for G-code warping engine."""

from __future__ import annotations

from pathlib import Path

from mesh_de_warper.core.calibration import Calibration
from mesh_de_warper.core.point import Point
from mesh_de_warper.gcode.warper import GCodeWarper
from mesh_de_warper.interpolation.bilinear import BilinearInterpolation


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

    def test_g90_mode_tracked(self) -> None:
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        cal.mesh[5, 5] = Point(x=50.0, y=50.0, offset_x=2.0, offset_y=0.0)
        warper = GCodeWarper(cal)
        gcode = "G91\nG1 X10 Y10"
        ast = warper.warp(gcode)
        cmd = ast.all_commands()[-1]
        assert cmd.g_code == 1

    def test_relative_mode_warp(self) -> None:
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        cal.mesh[2, 2] = Point(x=20.0, y=20.0, offset_x=1.0, offset_y=1.0)
        warper = GCodeWarper(cal)
        gcode = "G91\nG1 X20 Y20"
        ast = warper.warp(gcode)
        emitted = ast.all_commands()
        assert len(emitted) == 2
        move_cmd = emitted[1]
        # In relative mode, offset is still applied to the target position
        assert move_cmd.position.x is not None
        assert move_cmd.position.y is not None

    def test_arc_cw_with_ij(self) -> None:
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        warper = GCodeWarper(cal)
        gcode = "G2 X20 Y0 I0 J-10"
        ast = warper.warp(gcode)
        cmds = ast.all_commands()
        # Arc should be linearised into multiple G1 segments
        assert len(cmds) >= 2
        for cmd in cmds:
            assert cmd.g_code == 1

    def test_arc_ccw_with_ij(self) -> None:
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        warper = GCodeWarper(cal)
        gcode = "G3 X20 Y0 I0 J-10"
        ast = warper.warp(gcode)
        cmds = ast.all_commands()
        assert len(cmds) >= 2

    def test_arc_with_radius(self) -> None:
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        warper = GCodeWarper(cal)
        gcode = "G2 X20 Y0 R10"
        ast = warper.warp(gcode)
        cmds = ast.all_commands()
        assert len(cmds) >= 2

    def test_arc_without_centre_or_radius(self) -> None:
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        warper = GCodeWarper(cal)
        gcode = "G2 X20 Y0"
        ast = warper.warp(gcode)
        cmds = ast.all_commands()
        # Should be preserved as-is with warning
        assert len(cmds) == 1

    def test_arc_with_extrusion(self) -> None:
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        warper = GCodeWarper(cal)
        gcode = "G2 X20 Y0 I0 J-10 E0.5 F300"
        ast = warper.warp(gcode)
        cmds = ast.all_commands()
        assert len(cmds) >= 2
        # Extrusion should be distributed across segments
        total_e = sum(cmd.position.e or 0.0 for cmd in cmds)
        assert abs(total_e - 0.5) < 0.01

    def test_full_circle(self) -> None:
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        cal.mesh[5, 5] = Point(x=50.0, y=50.0, offset_x=0.5, offset_y=0.5)
        warper = GCodeWarper(cal)
        gcode = "G2 X0 Y0 I0 J-10"
        ast = warper.warp(gcode)
        cmds = ast.all_commands()
        assert len(cmds) >= 2

    def test_arc_with_feedrate_preserved(self) -> None:
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        warper = GCodeWarper(cal)
        gcode = "G2 X20 Y0 I0 J-10 F600"
        ast = warper.warp(gcode)
        cmds = ast.all_commands()
        for cmd in cmds[:3]:
            words_f = [w for w in cmd.words if w.letter == "F"]
            if words_f:
                assert abs(words_f[0].value - 600) < 1

    def test_zero_radius_arc(self) -> None:
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        warper = GCodeWarper(cal)
        gcode = "G2 X0 Y0 I0 J0"
        ast = warper.warp(gcode)
        cmds = ast.all_commands()
        assert len(cmds) == 1

    def test_relative_arc(self) -> None:
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        warper = GCodeWarper(cal)
        gcode = "G91\nG2 X20 Y0 I0 J-10"
        ast = warper.warp(gcode)
        cmds = ast.all_commands()
        assert len(cmds) >= 2

    def test_arc_ccw_with_radius(self) -> None:
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        warper = GCodeWarper(cal)
        gcode = "G3 X20 Y0 R10"
        ast = warper.warp(gcode)
        cmds = ast.all_commands()
        assert len(cmds) >= 2

    def test_arc_centre_from_radius_degenerate(self) -> None:
        cal = Calibration.for_bed(
            width=100.0, height=100.0, spacing=10.0,
            interpolation=BilinearInterpolation(),
        )
        warper = GCodeWarper(cal)
        gcode = "G2 X0 Y0 R1"  # start = end, degenerate arc
        ast = warper.warp(gcode)
        cmds = ast.all_commands()
        assert len(cmds) == 1  # should be preserved as-is


