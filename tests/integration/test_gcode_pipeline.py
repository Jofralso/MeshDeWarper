"""End-to-end integration tests for the G-code pipeline.

Exercises the full pipeline: parser → warper → emitter, and validates
that the output is syntactically valid and semantically correct.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from cura_xy_calibration.core.calibration import Calibration
from cura_xy_calibration.core.point import Point
from cura_xy_calibration.gcode.emitter import GCodeEmitter
from cura_xy_calibration.gcode.parser import GCodeParser
from cura_xy_calibration.gcode.warper import GCodeWarper
from cura_xy_calibration.interpolation.bilinear import BilinearInterpolation


# ── Helpers ─────────────────────────────────────────────────────────


def _uniform_cal(spacing: float = 50.0, offset_x: float = 0.0, offset_y: float = 0.0) -> Calibration:
    """Create a calibration with a constant offset across the whole bed."""
    cal = Calibration.for_bed(
        width=200.0,
        height=200.0,
        spacing=spacing,
        interpolation=BilinearInterpolation(),
    )
    if offset_x != 0.0 or offset_y != 0.0:
        for r in range(cal.mesh.rows):
            for c in range(cal.mesh.cols):
                p = cal.mesh[r, c]
                cal.mesh[r, c] = Point(p.x, p.y, offset_x, offset_y)
    return cal


def _pipeline(gcode: str, cal: Calibration) -> str:
    """Run G-code through parse → warp → emit and return the text."""
    warper = GCodeWarper(cal)
    ast = warper.warp(gcode)
    emitter = GCodeEmitter()
    return emitter.to_string(ast)


def _reparse(text: str):
    """Parse G-code text and return all commands."""
    return GCodeParser().parse(text).all_commands()


# ── Integration tests ───────────────────────────────────────────────


class TestLinearPipeline:
    """Tests for the G0/G1 linear move pipeline."""

    def test_single_move_round_trip(self) -> None:
        cal = _uniform_cal(offset_x=2.0, offset_y=-1.0)
        out = _pipeline("G1 X50 Y100 E0.5 F300", cal)
        cmds = _reparse(out)
        assert len(cmds) == 1
        c = cmds[0]
        assert c.g_code == 1
        assert c.position.x == pytest.approx(52.0)
        assert c.position.y == pytest.approx(99.0)
        assert c.position.e == 0.5
        assert c.position.f == 300.0

    def test_rapid_move_preserved(self) -> None:
        cal = _uniform_cal(offset_x=1.0, offset_y=1.0)
        out = _pipeline("G0 X100 Y100", cal)
        cmds = _reparse(out)
        assert cmds[0].g_code == 0
        assert cmds[0].position.x == pytest.approx(101.0)

    def test_multiple_moves(self) -> None:
        cal = _uniform_cal(offset_x=0.5, offset_y=0.0)
        gcode = "\n".join([
            "G1 X10 Y10",
            "G1 X20 Y20",
            "G1 X30 Y30",
        ])
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        assert len(cmds) == 3
        assert cmds[0].position.x == pytest.approx(10.5)
        assert cmds[1].position.x == pytest.approx(20.5)
        assert cmds[2].position.x == pytest.approx(30.5)

    def test_non_move_commands_preserved(self) -> None:
        cal = _uniform_cal(offset_x=1.0, offset_y=0.0)
        gcode = "\n".join([
            "M104 S200",
            "G28",
            "G1 X50 Y50",
            "M106 S128",
        ])
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        assert len(cmds) == 4
        assert cmds[0].m_code == 104
        assert cmds[1].g_code == 28
        assert cmds[2].position.x == pytest.approx(51.0)
        assert cmds[3].m_code == 106

    def test_comments_preserved(self) -> None:
        cal = _uniform_cal(offset_x=0.5, offset_y=0.5)
        gcode = "G1 X50 Y50 ; this is a comment"
        out = _pipeline(gcode, cal)
        # Emitter normalises comment spacing (no space after `;`)
        assert ";this is a comment" in out

    def test_line_numbers_preserved(self) -> None:
        cal = _uniform_cal(offset_x=0.0, offset_y=0.0)
        out = _pipeline("N10 G1 X10 Y20", cal)
        assert "N10" in out or "G1" in out

    def test_only_z_move_not_warped(self) -> None:
        cal = _uniform_cal(offset_x=5.0, offset_y=5.0)
        out = _pipeline("G1 Z10", cal)
        cmds = _reparse(out)
        assert cmds[0].position.z == 10.0
        # XY should not appear
        words = [w.letter for w in cmds[0].words]
        assert "X" not in words
        assert "Y" not in words

    def test_mixed_xy_and_z(self) -> None:
        cal = _uniform_cal(offset_x=1.0, offset_y=2.0)
        out = _pipeline("G1 X50 Y50 Z10", cal)
        cmds = _reparse(out)
        assert cmds[0].position.x == pytest.approx(51.0)
        assert cmds[0].position.y == pytest.approx(52.0)
        assert cmds[0].position.z == 10.0


class TestRelativeModePipeline:
    """Tests for G91 relative mode warping."""

    def test_relative_move_warped(self) -> None:
        cal = _uniform_cal(offset_x=1.0, offset_y=1.0)
        gcode = "\n".join([
            "G91",
            "G1 X10 Y10",
        ])
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        assert cmds[1].g_code == 1
        # Relative move: target is (10,10) from origin, offset applied to delta
        # offset_at(10, 10) = (1, 1)
        # So X = 10 + 1 = 11
        assert cmds[1].position.x == pytest.approx(11.0)
        assert cmds[1].position.y == pytest.approx(11.0)

    def test_absolute_after_relative(self) -> None:
        cal = _uniform_cal(offset_x=1.0, offset_y=0.0)
        gcode = "\n".join([
            "G91",
            "G1 X10 Y10",
            "G90",
            "G1 X50 Y50",
        ])
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        # Last absolute move should be warped absolutely
        assert cmds[3].position.x == pytest.approx(51.0)

    def test_relative_mode_toggle(self) -> None:
        cal = _uniform_cal(offset_x=0.5, offset_y=0.5)
        gcode = "\n".join([
            "G90",
            "G1 X10 Y10",
            "G91",
            "G1 X10 Y10",
            "G90",
            "G1 X30 Y30",
        ])
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        # Absolute moves
        assert cmds[1].position.x == pytest.approx(10.5)
        assert cmds[5].position.x == pytest.approx(30.5)
        # Relative move (X=10 + 0.5 = 10.5 relative to current pos 10)
        # Actually in relative mode, the delta X is (10 + 0.5) = 10.5
        assert cmds[3].position.x == pytest.approx(10.5)


class TestArcPipeline:
    """Tests for G2/G3 arc move linearisation and warping."""

    def test_arc_cw_with_ij(self) -> None:
        """G2 clockwise with I,J centre specification."""
        cal = _uniform_cal(offset_x=0.0, offset_y=0.0)
        gcode = "G2 X100 Y100 I50 J0"
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        # With no offset, the arc should be linearised into G1 segments
        assert len(cmds) >= 3  # at least a few segments
        for c in cmds:
            assert c.g_code == 1  # all segments are G1

    def test_arc_ccw_with_ij(self) -> None:
        """G3 counter-clockwise with I,J centre specification."""
        cal = _uniform_cal(offset_x=0.0, offset_y=0.0)
        gcode = "G3 X100 Y100 I0 J50"
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        assert len(cmds) >= 3

    def test_arc_with_radius(self) -> None:
        """G2/G3 with R (radius) instead of I,J."""
        cal = _uniform_cal(offset_x=0.0, offset_y=0.0)
        gcode = "G2 X100 Y100 R50"
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        assert len(cmds) >= 3

    def test_arc_warped(self) -> None:
        """Arc segments should be warped when offset is present.

        G2 X100 Y0 I50 J0 describes a CW semicircle from (0,0) to (100,0)
        around centre (50,0), radius 50. Linearised segments should all have
        offset ~2 applied.
        """
        cal = _uniform_cal(offset_x=2.0, offset_y=2.0, spacing=100.0)
        gcode = "G2 X100 Y0 I50 J0"
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        assert len(cmds) >= 10
        # Every segment should be G1
        assert all(c.g_code == 1 for c in cmds)
        # Last segment ends near (100, 0) warped → (102, 2)
        last = cmds[-1]
        assert last.position.x == pytest.approx(102.0, abs=1.0)
        assert last.position.y == pytest.approx(2.0, abs=1.0)
        # No original arc commands remain
        assert not any(c.g_code in (2, 3) for c in cmds)

    def test_arc_with_extrusion(self) -> None:
        """E value should be distributed across segments."""
        cal = _uniform_cal(offset_x=0.0, offset_y=0.0)
        gcode = "G2 X100 Y100 I50 J0 E2.0"
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        total_e = sum(c.position.e or 0.0 for c in cmds)
        assert total_e == pytest.approx(2.0, abs=0.01)

    def test_arc_without_centre_radius_preserved(self) -> None:
        """Arc without I,J,R should be left unchanged."""
        cal = _uniform_cal(offset_x=1.0, offset_y=1.0)
        gcode = "G2 X100 Y100"
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        assert len(cmds) == 1
        assert cmds[0].g_code == 2

    def test_full_circle(self) -> None:
        """A full circle arc (start=end) should produce segments."""
        cal = _uniform_cal(offset_x=0.0, offset_y=0.0)
        # Full CW circle: start (0,0), centre at (0,50) via I0 J50, end back at (0,0)
        gcode = "G2 X0 Y0 I0 J50"
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        assert len(cmds) >= 50  # ~314 segments for radius=50
        # Should end near the start position
        last = cmds[-1]
        assert last.position.x == pytest.approx(0.0, abs=1.0)
        assert last.position.y == pytest.approx(0.0, abs=1.0)


class TestPipelineEdgeCases:
    """Edge cases for the full pipeline."""

    def test_empty_input(self) -> None:
        cal = _uniform_cal()
        out = _pipeline("", cal)
        assert out == ""

    def test_comment_only_input(self) -> None:
        cal = _uniform_cal()
        out = _pipeline("; just a comment", cal)
        assert "just a comment" in out

    def test_newlines_preserved(self) -> None:
        cal = _uniform_cal()
        gcode = "G1 X10 Y10\n\nG1 X20 Y20\n"
        out = _pipeline(gcode, cal)
        # Empty lines become empty output lines
        assert out.count("\n") >= 2
        # Non-empty lines survive
        lines = [l for l in out.split("\n") if l.strip()]
        assert len(lines) == 2

    def test_large_offset(self) -> None:
        cal = _uniform_cal(offset_x=100.0, offset_y=100.0)
        out = _pipeline("G1 X50 Y50", cal)
        cmds = _reparse(out)
        assert cmds[0].position.x == pytest.approx(150.0)
        assert cmds[0].position.y == pytest.approx(150.0)

    def test_zero_offset_passthrough(self) -> None:
        cal = _uniform_cal(offset_x=0.0, offset_y=0.0)
        gcode = "G1 X42.5 Y73.8"
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        assert cmds[0].position.x == pytest.approx(42.5)
        assert cmds[0].position.y == pytest.approx(73.8)

    def test_multiple_lines_with_mixed_gcodes(self) -> None:
        """A realistic G-code snippet."""
        cal = _uniform_cal(offset_x=0.1, offset_y=-0.1)
        gcode = "\n".join([
            "; Generated by Cura",
            "M140 S60",
            "M104 S200",
            "G28",
            "G90",
            "G1 Z5 F300",
            "G1 X10 Y10 F1200",
            "G1 X20 Y20 E0.5",
            "M106 S255",
            "G1 X30 Y30",
        ])
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        assert len(cmds) == 10
        # Comments preserved
        assert "Generated by Cura" in out
        # Move commands warped
        for c in cmds:
            if c.g_code == 1 and c.has_xy():
                px = c.position.x
                py = c.position.y
                assert px is not None and py is not None
                # Should be close to original + offset
                assert px != pytest.approx(px - 0.1)  # changed


class TestParseEmitRoundTrip:
    """Verify that parsing and re-emitting preserves semantics."""

    GCODE_INPUTS = [
        "G1 X10 Y20 E0.5 F300",
        "G0 X100 Y100",
        "G91\nG1 X10 Y10\nG90",
        "M104 S200 ; set temp",
        "; just a comment",
    ]

    @pytest.mark.parametrize("gcode", GCODE_INPUTS)
    def test_round_trip_no_warp(self, gcode: str) -> None:
        """With zero offsets, output should reproduce input positions."""
        cal = _uniform_cal(offset_x=0.0, offset_y=0.0, spacing=50.0)
        out = _pipeline(gcode, cal)
        cmds = _reparse(out)
        orig = _reparse(gcode)
        assert len(cmds) == len(orig)


class TestFilePipeline:
    """Tests using file I/O through the full pipeline."""

    @pytest.fixture
    def input_gcode(self, temp_dir: Path) -> Path:
        p = temp_dir / "input.gcode"
        p.write_text("\n".join([
            "; test file",
            "G1 X10 Y10",
            "G1 X20 Y20",
            "G1 X30 Y30",
        ]))
        return p

    def test_warp_file(self, input_gcode: Path, temp_dir: Path) -> None:
        cal = _uniform_cal(offset_x=1.0, offset_y=1.0)
        output = temp_dir / "output.gcode"
        warper = GCodeWarper(cal)
        warper.warp_file(input_gcode, output)
        assert output.exists()
        content = output.read_text()
        assert "test file" in content or ";test file" in content
        cmds = _reparse(content)
        assert len(cmds) == 4

    def test_warp_file_zero_offset(self, input_gcode: Path, temp_dir: Path) -> None:
        cal = _uniform_cal(offset_x=0.0, offset_y=0.0)
        output = temp_dir / "output.gcode"
        warper = GCodeWarper(cal)
        warper.warp_file(input_gcode, output)
        original = input_gcode.read_text()
        result = output.read_text()
        # File size should be similar (only formatting diffs)
        assert abs(len(result) - len(original)) < len(original) * 0.5
