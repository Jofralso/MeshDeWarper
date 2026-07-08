"""G-code parser producing a structured AST."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from pathlib import Path

from mesh_de_warper.gcode.ast import GCodeAst, GCodeBlock, GCodeCommand, GCodeWord

logger = logging.getLogger(__name__)

LINE_RE = re.compile(r"^\s*(N\d+\s+)?(?P<body>[^;]*)(;.*)?$")
WORD_RE = re.compile(r"(?P<letter>[A-Z])(?P<value>-?\d+(?:\.\d+)?)")


class GCodeParser:
    """Parser that converts G-code text into a structured AST.

    The parser produces a streaming AST that preserves formatting
    and comments. It handles absolute and relative modes.
    """

    def __init__(self) -> None:
        self._line_number = 0

    def parse(self, source: str | Path) -> GCodeAst:
        """Parse a G-code string or file into an AST."""
        if isinstance(source, Path):
            text = source.read_text()
        else:
            text = source

        self._line_number = 0
        ast = GCodeAst()
        current_block = GCodeBlock()

        for line in text.splitlines():
            self._line_number += 1
            cmd = self._parse_line(line)
            current_block.commands.append(cmd)

        if current_block.commands:
            ast.blocks.append(current_block)

        logger.debug("Parsed %d commands from %d lines", len(ast), self._line_number)
        return ast

    def parse_stream(self, lines: Iterator[str]) -> Iterator[GCodeCommand]:
        """Parse an iterable of lines, yielding commands one at a time."""
        self._line_number = 0
        for line in lines:
            self._line_number += 1
            yield self._parse_line(line)

    def _parse_line(self, line: str) -> GCodeCommand:
        """Parse a single line into a GCodeCommand."""
        match = LINE_RE.match(line)
        if not match:  # pragma: no cover
            return GCodeCommand(
                words=[],
                comment="",
                raw=line,
                line_number=self._line_number,
            )

        body = match.group("body").strip()
        comment = match.group(3) or ""

        words = []
        for wm in WORD_RE.finditer(body):
            letter = wm.group("letter")
            value = float(wm.group("value"))
            words.append(GCodeWord(letter=letter, value=value))

        return GCodeCommand(
            words=words,
            comment=comment.strip().lstrip(";").strip(),
            raw=line,
            line_number=self._line_number,
        )
