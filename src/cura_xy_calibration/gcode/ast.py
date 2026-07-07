"""AST data types for G-code representation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class MoveType(Enum):
    """Type of G-code move."""

    RAPID = auto()
    LINEAR = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class Position:
    """A 3D position with extrusion amount."""

    x: float | None = None
    y: float | None = None
    z: float | None = None
    e: float | None = None
    f: float | None = None

    def has_xy(self) -> bool:
        return self.x is not None and self.y is not None


@dataclass(frozen=True)
class GCodeWord:
    """A single G-code word, e.g. 'G', 'X', 'Y', 'E'."""

    letter: str
    value: float

    def __str__(self) -> str:
        val = self.value
        if val == int(val):
            return f"{self.letter}{int(val)}"
        return f"{self.letter}{val:g}"


@dataclass
class GCodeCommand:
    """A single G-code command (line), e.g. 'G1 X10 Y20 E0.5'."""

    words: list[GCodeWord] = field(default_factory=list)
    comment: str = ""
    raw: str = ""
    line_number: int = 0

    @property
    def g_code(self) -> int | None:
        for w in self.words:
            if w.letter == "G":
                return int(w.value)
        return None

    @property
    def m_code(self) -> int | None:
        for w in self.words:
            if w.letter == "M":
                return int(w.value)
        return None

    @property
    def position(self) -> Position:
        pos = Position()
        for w in self.words:
            if w.letter == "X":
                pos = Position(x=w.value, y=pos.y, z=pos.z, e=pos.e, f=pos.f)
            elif w.letter == "Y":
                pos = Position(x=pos.x, y=w.value, z=pos.z, e=pos.e, f=pos.f)
            elif w.letter == "Z":
                pos = Position(x=pos.x, y=pos.y, z=w.value, e=pos.e, f=pos.f)
            elif w.letter == "E":
                pos = Position(x=pos.x, y=pos.y, z=pos.z, e=w.value, f=pos.f)
            elif w.letter == "F":
                pos = Position(x=pos.x, y=pos.y, z=pos.z, e=pos.e, f=w.value)
        return pos

    @property
    def move_type(self) -> MoveType:
        g = self.g_code
        if g == 0:
            return MoveType.RAPID
        elif g == 1:
            return MoveType.LINEAR
        return MoveType.UNKNOWN

    def is_move(self) -> bool:
        return self.g_code in (0, 1)

    def has_xy(self) -> bool:
        return any(w.letter == "X" for w in self.words) or any(w.letter == "Y" for w in self.words)

    def __str__(self) -> str:
        parts = [str(w) for w in self.words]
        line = " ".join(parts)
        if self.comment:
            line += f" ;{self.comment}"
        return line


@dataclass
class GCodeBlock:
    """A logical block of G-code (sequence of commands)."""

    commands: list[GCodeCommand] = field(default_factory=list)

    def __str__(self) -> str:
        return "\n".join(str(c) for c in self.commands)


@dataclass
class GCodeAst:
    """Complete AST for a G-code program."""

    blocks: list[GCodeBlock] = field(default_factory=list)

    def __len__(self) -> int:
        return sum(len(b.commands) for b in self.blocks)

    def all_commands(self) -> list[GCodeCommand]:
        return [cmd for block in self.blocks for cmd in block.commands]

    def __str__(self) -> str:
        return "\n".join(str(b) for b in self.blocks)
