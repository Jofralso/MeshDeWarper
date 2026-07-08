"""G-code warping engine — applies distortion correction to G-code."""

from __future__ import annotations

import logging
import math
from pathlib import Path

from mesh_de_warper.core.calibration import Calibration
from mesh_de_warper.gcode.ast import (
    GCodeAst,
    GCodeCommand,
    GCodeWord,
    MoveType,
    Position,
)
from mesh_de_warper.gcode.emitter import GCodeEmitter
from mesh_de_warper.gcode.parser import GCodeParser

logger = logging.getLogger(__name__)

_ARC_SEGMENT_LENGTH = 1.0  # mm — maximum arc segment length for linearisation


class GCodeWarper:
    """Applies distortion correction to G-code using a Calibration mesh.

    Transforms XY coordinates in G0/G1/G2/G3 moves while preserving all
    other parameters, formatting, and comments. Handles both absolute
    and relative positioning modes. Arc moves (G2/G3) are linearised into
    small G1 segments before warping.
    """

    def __init__(
        self, calibration: Calibration, arc_segment_length: float = _ARC_SEGMENT_LENGTH
    ) -> None:
        self._calibration = calibration
        self._absolute_mode = True
        self._arc_segment_length = arc_segment_length

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
            new_commands: list[GCodeCommand] = []
            for cmd in block.commands:
                result = self._process_command(cmd, current_pos)
                if result:
                    new_commands.extend(result)
                current_pos = self._update_position(current_pos, cmd)
            block.commands = new_commands

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
    ) -> list[GCodeCommand]:
        """Apply distortion correction to a single command.

        Returns a list of (possibly multiple) replacement commands.
        An empty list means the command should be removed.
        """
        if not cmd.is_move():
            if cmd.g_code == 90:
                self._absolute_mode = True
            elif cmd.g_code == 91:
                self._absolute_mode = False
            return [cmd]

        move_type = cmd.move_type
        if move_type in (MoveType.ARC_CW, MoveType.ARC_CCW):
            return self._warp_arc(cmd, current_pos)

        return self._warp_linear(cmd, current_pos)

    def _warp_linear(
        self,
        cmd: GCodeCommand,
        current_pos: Position,
    ) -> list[GCodeCommand]:
        """Apply distortion to a linear (G0/G1) move."""
        pos = cmd.position
        has_x = any(w.letter == "X" for w in cmd.words)
        has_y = any(w.letter == "Y" for w in cmd.words)

        if not has_x and not has_y:
            return [cmd]

        if self._absolute_mode:
            target_x = pos.x if pos.x is not None else current_pos.x
            target_y = pos.y if pos.y is not None else current_pos.y
        else:
            target_x = (current_pos.x or 0.0) + (pos.x or 0.0)
            target_y = (current_pos.y or 0.0) + (pos.y or 0.0)

        if target_x is None or target_y is None:
            return [cmd]

        off_x, off_y = self._calibration.offset_at(target_x, target_y)

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

        return [cmd]

    def _warp_arc(
        self,
        cmd: GCodeCommand,
        current_pos: Position,
    ) -> list[GCodeCommand]:
        """Linearise an arc (G2/G3) into warped G1 segments."""
        is_cw = cmd.move_type == MoveType.ARC_CW
        pos = cmd.position
        arc = cmd.arc_params

        # Resolve start and end positions in absolute coordinates
        if self._absolute_mode:
            start_x = current_pos.x or 0.0
            start_y = current_pos.y or 0.0
            end_x = pos.x if pos.x is not None else start_x
            end_y = pos.y if pos.y is not None else start_y
        else:
            start_x = current_pos.x or 0.0
            start_y = current_pos.y or 0.0
            end_x = start_x + (pos.x or 0.0)
            end_y = start_y + (pos.y or 0.0)

        # Determine centre, radius, and angles
        if arc.is_center_specified:
            cx = start_x + arc.i  # type: ignore[operator]
            cy = start_y + arc.j  # type: ignore[operator]
        elif arc.is_radius_specified:
            center = self._arc_center_from_radius(
                start_x,
                start_y,
                end_x,
                end_y,
                arc.r if arc.r is not None else 0.0,
                is_cw,
            )
            cx, cy = center
        else:
            logger.warning("Arc has neither I/J nor R; skipping warping")
            return [cmd]

        radius = math.hypot(start_x - cx, start_y - cy)
        if radius < 1e-12:
            return [cmd]

        start_angle = math.atan2(start_y - cy, start_x - cx)
        end_angle = math.atan2(end_y - cy, end_x - cx)

        # Normalise angular range
        if is_cw:
            while end_angle > start_angle - 1e-12:
                end_angle -= 2.0 * math.pi
        else:
            while end_angle < start_angle + 1e-12:
                end_angle += 2.0 * math.pi

        total_angle = abs(end_angle - start_angle)
        arc_length = radius * total_angle
        num_segments = max(1, round(arc_length / self._arc_segment_length))
        angular_step = (end_angle - start_angle) / num_segments

        # Preserve E and F from original command
        orig_e = pos.e
        orig_f = pos.f

        # Distribute E proportionally across segments
        e_per_seg = (orig_e / num_segments) if orig_e is not None else None

        segments: list[GCodeCommand] = []
        for i in range(1, num_segments + 1):
            angle = start_angle + angular_step * i
            seg_x = cx + radius * math.cos(angle)
            seg_y = cy + radius * math.sin(angle)

            # Warp the segment endpoint
            off_x, off_y = self._calibration.offset_at(seg_x, seg_y)

            words: list[GCodeWord] = [GCodeWord("G", 1)]
            if self._absolute_mode:
                words.append(GCodeWord("X", round(seg_x + off_x, 4)))
                words.append(GCodeWord("Y", round(seg_y + off_y, 4)))
            else:
                dx = seg_x - start_x
                dy = seg_y - start_y
                words.append(GCodeWord("X", round(dx + off_x, 4)))
                words.append(GCodeWord("Y", round(dy + off_y, 4)))

            if e_per_seg is not None:
                words.append(GCodeWord("E", round(e_per_seg, 5)))
            if orig_f is not None:
                words.append(GCodeWord("F", round(orig_f, 2)))

            seg_cmd = GCodeCommand(words=words, comment=cmd.comment, line_number=cmd.line_number)
            seg_cmd.raw = str(seg_cmd)
            segments.append(seg_cmd)

        return segments

    @staticmethod
    def _arc_center_from_radius(
        x1: float, y1: float, x2: float, y2: float, r: float, cw: bool
    ) -> tuple[float, float]:
        """Compute arc centre from two endpoints and radius.

        See https://math.stackexchange.com/a/1781546
        """
        dx = x2 - x1
        dy = y2 - y1
        d = math.hypot(dx, dy)
        if d < 1e-12:
            return (x1, y1)

        # Midpoint
        mx = (x1 + x2) / 2.0
        my = (y1 + y2) / 2.0

        # Distance from midpoint to centre
        h = math.sqrt(max(0.0, r * r - (d / 2.0) ** 2))

        # Perpendicular unit
        px = -dy / d
        py = dx / d

        if cw:
            cx = mx + px * h
            cy = my + py * h
        else:
            cx = mx - px * h
            cy = my - py * h

        return (cx, cy)

    @staticmethod
    def _set_word(cmd: GCodeCommand, letter: str, value: float) -> None:
        """Set or update a word in the command."""
        for w in cmd.words:
            if w.letter == letter:
                idx = cmd.words.index(w)
                cmd.words[idx] = GCodeWord(letter=letter, value=round(value, 4))
                return
        cmd.words.append(GCodeWord(letter=letter, value=round(value, 4)))  # pragma: no cover

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
