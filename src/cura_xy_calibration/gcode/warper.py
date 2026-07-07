"""G-code warping engine — applies distortion correction to G-code."""

from __future__ import annotations

import logging
from pathlib import Path

from cura_xy_calibration.core.calibration import Calibration
from cura_xy_calibration.gcode.ast import GCodeAst, GCodeCommand, GCodeWord, Position
from cura_xy_calibration.gcode.emitter import GCodeEmitter
from cura_xy_calibration.gcode.parser import GCodeParser

logger = logging.getLogger(__name__)


class GCodeWarper:
    """Applies distortion correction to G-code using a Calibration mesh.

    Transforms XY coordinates in G0/G1 moves while preserving all other
    parameters, formatting, and comments. Handles both absolute and
    relative positioning modes.
    """

    def __init__(self, calibration: Calibration) -> None:
        self._calibration = calibration
        self._absolute_mode = True

    def warp(self, source: str | Path) -> GCodeAst:
        """Parse and warp G-code, returning the corrected AST."""
        if isinstance(source, Path):
            text = source.read_text()
        else:
            text = source

        parser = GCodeParser()
        ast = parser.parse(text)
        return self.warp_ast(ast)

    def warp_ast(self, ast: GCodeAst) -> GCodeAst:
        """Warp an already-parsed AST in place and return it."""
        current_pos = Position(x=0.0, y=0.0, z=0.0, e=0.0)
        self._absolute_mode = True

        for block in ast.blocks:
            for cmd in block.commands:
                self._process_command(cmd, current_pos)
                current_pos = self._update_position(current_pos, cmd)

        return ast

    def warp_file(self, input_path: Path, output_path: Path) -> None:
        """Read, warp, and write a G-code file."""
        ast = self.warp(input_path)
        emitter = GCodeEmitter()
        emitter.emit(ast, output_path)
        logger.info(
            "Warped %s -> %s (%d commands)",
            input_path,
            output_path,
            len(ast),
        )

    def _process_command(
        self,
        cmd: GCodeCommand,
        current_pos: Position,
    ) -> None:
        """Apply distortion correction to a single command."""
        if not cmd.is_move():
            # Check for G90/G91 mode changes
            if cmd.g_code == 90:
                self._absolute_mode = True
            elif cmd.g_code == 91:
                self._absolute_mode = False
            return

        pos = cmd.position
        has_x = any(w.letter == "X" for w in cmd.words)
        has_y = any(w.letter == "Y" for w in cmd.words)

        if not has_x and not has_y:
            return

        # Resolve absolute position
        if self._absolute_mode:
            target_x = pos.x if pos.x is not None else current_pos.x
            target_y = pos.y if pos.y is not None else current_pos.y
        else:
            target_x = (current_pos.x or 0.0) + (pos.x or 0.0)
            target_y = (current_pos.y or 0.0) + (pos.y or 0.0)

        assert target_x is not None
        assert target_y is not None

        # Get correction offset
        off_x, off_y = self._calibration.offset_at(target_x, target_y)

        # Apply correction
        if self._absolute_mode:
            if has_x:
                self._set_word(cmd, "X", target_x + off_x)
            if has_y:
                self._set_word(cmd, "Y", target_y + off_y)
        else:
            if has_x:
                self._set_word(cmd, "X", (pos.x or 0.0) + off_x)
            if has_y:
                self._set_word(cmd, "Y", (pos.y or 0.0) + off_y)

    @staticmethod
    def _set_word(cmd: GCodeCommand, letter: str, value: float) -> None:
        """Set or update a word in the command."""
        for w in cmd.words:
            if w.letter == letter:
                # We need to replace the word since GCodeWord is frozen
                idx = cmd.words.index(w)
                cmd.words[idx] = GCodeWord(letter=letter, value=round(value, 4))
                return
        cmd.words.append(GCodeWord(letter=letter, value=round(value, 4)))

    @staticmethod
    def _update_position(current: Position, cmd: GCodeCommand) -> Position:
        """Update position tracking after processing a command."""
        pos = cmd.position
        return Position(
            x=pos.x if pos.x is not None else current.x,
            y=pos.y if pos.y is not None else current.y,
            z=pos.z if pos.z is not None else current.z,
            e=pos.e if pos.e is not None else current.e,
            f=pos.f if pos.f is not None else current.f or current.f,
        )
