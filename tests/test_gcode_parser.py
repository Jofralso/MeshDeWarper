"""Tests for G-code parser."""

from __future__ import annotations

from cura_xy_calibration.gcode.parser import GCodeParser


class TestGCodeParser:
    def test_parse_simple_gcode(self) -> None:
        text = "G1 X10 Y20 E0.5 F300"
        parser = GCodeParser()
        ast = parser.parse(text)
        assert len(ast) == 1
        cmd = ast.all_commands()[0]
        assert cmd.g_code == 1
        assert cmd.position.x == 10.0
        assert cmd.position.y == 20.0
        assert cmd.position.e == 0.5
        assert cmd.position.f == 300.0

    def test_parse_with_comments(self) -> None:
        text = "G1 X10 ; move to X10"
        parser = GCodeParser()
        ast = parser.parse(text)
        cmd = ast.all_commands()[0]
        assert cmd.comment == "move to X10"
        assert cmd.g_code == 1

    def test_parse_multiple_lines(self) -> None:
        text = "G0 Z5\nG1 X10 Y20\nM104 S200"
        parser = GCodeParser()
        ast = parser.parse(text)
        assert len(ast) == 3
        cmds = ast.all_commands()
        assert cmds[0].g_code == 0
        assert cmds[1].g_code == 1
        assert cmds[2].m_code == 104

    def test_parse_empty_lines(self) -> None:
        text = "G1 X10\n\nG1 Y20\n"
        parser = GCodeParser()
        ast = parser.parse(text)
        assert len(ast) == 3

    def test_parse_comment_only_line(self) -> None:
        text = "; this is a comment\nG1 X10"
        parser = GCodeParser()
        ast = parser.parse(text)
        assert len(ast) == 2
        assert ast.all_commands()[0].comment == "this is a comment"
        assert ast.all_commands()[0].g_code is None

    def test_parse_negative_values(self) -> None:
        text = "G1 X-10 Y-20"
        parser = GCodeParser()
        ast = parser.parse(text)
        cmd = ast.all_commands()[0]
        assert cmd.position.x == -10.0
        assert cmd.position.y == -20.0

    def test_parse_line_numbers(self) -> None:
        text = "N10 G1 X10\nN20 G1 Y20"
        parser = GCodeParser()
        ast = parser.parse(text)
        assert len(ast) == 2

    def test_preserves_raw(self) -> None:
        text = "  G1  X10  Y20  "
        parser = GCodeParser()
        ast = parser.parse(text)
        cmd = ast.all_commands()[0]
        assert cmd.raw == text

    def test_parse_stream(self) -> None:
        parser = GCodeParser()
        lines = ["G1 X10", "G1 Y20", "G1 Z5"]
        cmds = list(parser.parse_stream(iter(lines)))
        assert len(cmds) == 3
        assert cmds[0].g_code == 1
        assert cmds[0].position.x == 10.0
