"""Tests for G-code AST data types."""

from __future__ import annotations

from mesh_de_warper.gcode.ast import (
    GCodeAst,
    GCodeBlock,
    GCodeCommand,
    GCodeWord,
    MoveType,
    Position,
)


class TestGCodeWord:
    def test_string_int(self) -> None:
        w = GCodeWord(letter="G", value=1.0)
        assert str(w) == "G1"

    def test_string_float(self) -> None:
        w = GCodeWord(letter="X", value=10.5)
        assert str(w) == "X10.5"


class TestPosition:
    def test_has_xy(self) -> None:
        assert Position(x=1.0, y=2.0).has_xy()
        assert not Position(x=1.0).has_xy()
        assert not Position().has_xy()

    def test_partial_position(self) -> None:
        pos = Position(x=10.0)
        assert pos.x == 10.0
        assert pos.y is None


class TestGCodeCommand:
    def test_g_code(self) -> None:
        cmd = GCodeCommand(words=[GCodeWord("G", 1), GCodeWord("X", 10.0)])
        assert cmd.g_code == 1

    def test_m_code(self) -> None:
        cmd = GCodeCommand(words=[GCodeWord("M", 104)])
        assert cmd.m_code == 104

    def test_no_g_code(self) -> None:
        cmd = GCodeCommand(words=[GCodeWord("X", 10.0)])
        assert cmd.g_code is None

    def test_no_m_code(self) -> None:
        cmd = GCodeCommand(words=[GCodeWord("G", 1)])
        assert cmd.m_code is None

    def test_position(self) -> None:
        cmd = GCodeCommand(
            words=[
                GCodeWord("G", 1),
                GCodeWord("X", 10.0),
                GCodeWord("Y", 20.0),
                GCodeWord("E", 0.5),
                GCodeWord("F", 300.0),
            ]
        )
        pos = cmd.position
        assert pos.x == 10.0
        assert pos.y == 20.0
        assert pos.e == 0.5
        assert pos.f == 300.0

    def test_move_type(self) -> None:
        g0 = GCodeCommand(words=[GCodeWord("G", 0)])
        g1 = GCodeCommand(words=[GCodeWord("G", 1)])
        unknown = GCodeCommand(words=[GCodeWord("M", 104)])
        assert g0.move_type == MoveType.RAPID
        assert g1.move_type == MoveType.LINEAR
        assert unknown.move_type == MoveType.UNKNOWN

    def test_is_move(self) -> None:
        assert GCodeCommand(words=[GCodeWord("G", 0)]).is_move()
        assert GCodeCommand(words=[GCodeWord("G", 1)]).is_move()
        assert not GCodeCommand(words=[GCodeWord("M", 104)]).is_move()

    def test_has_xy(self) -> None:
        cmd = GCodeCommand(words=[GCodeWord("X", 10.0)])
        assert cmd.has_xy()
        cmd2 = GCodeCommand(words=[GCodeWord("G", 1)])
        assert not cmd2.has_xy()

    def test_string_with_comment(self) -> None:
        cmd = GCodeCommand(
            words=[GCodeWord("G", 1), GCodeWord("X", 10.0)],
            comment="test comment",
        )
        s = str(cmd)
        assert "G1" in s
        assert "X10" in s
        assert "test comment" in s


class TestGCodeAst:
    def test_len(self) -> None:
        ast = GCodeAst(
            blocks=[
                GCodeBlock(commands=[GCodeCommand(), GCodeCommand()]),
                GCodeBlock(commands=[GCodeCommand()]),
            ]
        )
        assert len(ast) == 3

    def test_all_commands(self) -> None:
        c1, c2 = GCodeCommand(), GCodeCommand()
        ast = GCodeAst(
            blocks=[
                GCodeBlock(commands=[c1]),
                GCodeBlock(commands=[c2]),
            ]
        )
        assert ast.all_commands() == [c1, c2]
