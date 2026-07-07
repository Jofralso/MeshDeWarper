"""Tests for G-code emitter."""

from __future__ import annotations

from pathlib import Path

from cura_xy_calibration.gcode.ast import GCodeAst, GCodeBlock, GCodeCommand, GCodeWord
from cura_xy_calibration.gcode.emitter import GCodeEmitter


class TestGCodeEmitter:
    def test_emit_single_command(self) -> None:
        ast = GCodeAst(
            blocks=[
                GCodeBlock(
                    commands=[
                        GCodeCommand(
                            words=[GCodeWord("G", 1), GCodeWord("X", 10.5)],
                            raw="G1 X10.5",
                        ),
                    ]
                ),
            ]
        )
        emitter = GCodeEmitter()
        result = emitter.to_string(ast)
        assert "G1" in result
        assert "X10.5" in result

    def test_emit_with_comment(self) -> None:
        ast = GCodeAst(
            blocks=[
                GCodeBlock(
                    commands=[
                        GCodeCommand(
                            words=[GCodeWord("G", 1)],
                            comment="test comment",
                            raw="G1 ;test comment",
                        ),
                    ]
                ),
            ]
        )
        emitter = GCodeEmitter()
        result = emitter.to_string(ast)
        assert "test comment" in result

    def test_emit_to_file(self, temp_dir: Path) -> None:
        ast = GCodeAst(
            blocks=[
                GCodeBlock(
                    commands=[
                        GCodeCommand(
                            words=[GCodeWord("G", 1), GCodeWord("X", 10.0)],
                            raw="G1 X10",
                        ),
                    ]
                ),
            ]
        )
        emitter = GCodeEmitter()
        path = temp_dir / "output.gcode"
        emitter.emit(ast, path)
        assert path.exists()
        content = path.read_text()
        assert "G1 X10" in content

    def test_emit_empty_ast(self) -> None:
        ast = GCodeAst()
        emitter = GCodeEmitter()
        result = emitter.to_string(ast)
        assert result == ""

    def test_emit_comment_only(self) -> None:
        ast = GCodeAst(
            blocks=[
                GCodeBlock(
                    commands=[
                        GCodeCommand(comment="just a comment", raw=";just a comment"),
                    ]
                ),
            ]
        )
        emitter = GCodeEmitter()
        result = emitter.to_string(ast)
        assert "just a comment" in result
