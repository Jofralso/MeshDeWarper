"""G-code emitter — writes AST back to formatted G-code text."""

from __future__ import annotations

import logging
from pathlib import Path

from mesh_de_warper.gcode.ast import GCodeAst, GCodeCommand

logger = logging.getLogger(__name__)


class GCodeEmitter:
    """Emits formatted G-code text from an AST.

    Preserves original formatting, word order, and comments.
    Output uses standard G-code formatting conventions.
    """

    def emit(self, ast: GCodeAst, output: str | Path) -> None:
        """Write the AST to a file as formatted G-code."""
        text = self.to_string(ast)
        if isinstance(output, str):
            output = Path(output)
        output.write_text(text)
        logger.debug("Emitted %d commands to %s", len(ast), output)

    def to_string(self, ast: GCodeAst) -> str:
        """Convert AST to a formatted G-code string."""
        lines: list[str] = []
        for block in ast.blocks:
            for cmd in block.commands:
                if cmd.raw:
                    lines.append(self._format_command(cmd))
                else:
                    lines.append("")
        return "\n".join(lines)

    def _format_command(self, cmd: GCodeCommand) -> str:
        """Format a single command, preserving original where possible."""
        if not cmd.words and not cmd.comment:
            return cmd.raw

        parts = [str(w) for w in cmd.words]
        line = " ".join(parts) if parts else ""

        if cmd.comment:
            if parts:
                line += f" ;{cmd.comment}"
            else:
                line = f";{cmd.comment}"

        return line
