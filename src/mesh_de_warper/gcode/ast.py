"""AST data types for G-code representation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class MoveType(Enum):
    """Type of G-code move."""

    RAPID = auto()
    LINEAR = auto()
    ARC_CW = auto()
    ARC_CCW = auto()
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
        """Check if both X and Y coordinates are set."""
        return self.x is not None and self.y is not None


@dataclass(frozen=True)
class GCodeWord:
    """A single G-code word, e.g. 'G', 'X', 'Y', 'E'."""

    letter: str
    value: float

    def __str__(self) -> str:
        """Format word with integer shorthand when applicable."""
        val = self.value
        if val == int(val):
            return f"{self.letter}{int(val)}"
        return f"{self.letter}{val:g}"


@dataclass(frozen=True)
class ArcParams:
    """Parameters for G2/G3 arc moves.

    Attributes:
        i: X-centre offset from start.
        j: Y-centre offset from start.
        r: Radius (alternative to I/J).
    """

    i: float | None = None
    j: float | None = None
    r: float | None = None

    @property
    def is_center_specified(self) -> bool:
        """Check if I/J centre offsets are provided."""
        return self.i is not None and self.j is not None

    @property
    def is_radius_specified(self) -> bool:
        """Check if radius is provided."""
        return self.r is not None


@dataclass
class GCodeCommand:
    """A single G-code command (line), e.g. 'G1 X10 Y20 E0.5'."""

    words: list[GCodeWord] = field(default_factory=list)
    comment: str = ""
    raw: str = ""
    line_number: int = 0

    @property
    def g_code(self) -> int | None:
        """Extract G-code number (e.g., 1 from G1)."""
        for w in self.words:
            if w.letter == "G":
                return int(w.value)
        return None

    @property
    def m_code(self) -> int | None:
        """Extract M-code number (e.g., 106 from M106)."""
        for w in self.words:
            if w.letter == "M":
                return int(w.value)
        return None

    @property
    def position(self) -> Position:
        """Extract the position from command words."""
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
        """Classify the move type (rapid, linear, arc)."""
        g = self.g_code
        if g == 0:
            return MoveType.RAPID
        elif g == 1:
            return MoveType.LINEAR
        elif g == 2:
            return MoveType.ARC_CW
        elif g == 3:
            return MoveType.ARC_CCW
        return MoveType.UNKNOWN

    @property
    def arc_params(self) -> ArcParams:
        """Extract arc parameters (I, J, R) from the command."""
        i_val: float | None = None
        j_val: float | None = None
        r_val: float | None = None
        for w in self.words:
            if w.letter == "I":
                i_val = w.value
            elif w.letter == "J":
                j_val = w.value
            elif w.letter == "R":
                r_val = w.value
        return ArcParams(i=i_val, j=j_val, r=r_val)

    def is_move(self) -> bool:
        """Check if this is a movement command (G0, G1, G2, G3)."""
        return self.g_code in (0, 1, 2, 3)

    def has_xy(self) -> bool:
        """Check if the command contains X or Y words."""
        return any(w.letter == "X" for w in self.words) or any(w.letter == "Y" for w in self.words)

    def __str__(self) -> str:
        """Format command as a G-code line string."""
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
        """Format block as newline-separated command string."""
        return "\n".join(str(c) for c in self.commands)


@dataclass
class GCodeAst:
    """Complete AST for a G-code program."""

    blocks: list[GCodeBlock] = field(default_factory=list)

    def __len__(self) -> int:
        """Return total command count across all blocks."""
        return sum(len(b.commands) for b in self.blocks)

    def all_commands(self) -> list[GCodeCommand]:
        """Get a flat list of all commands across all blocks."""
        return [cmd for block in self.blocks for cmd in block.commands]

    def __str__(self) -> str:
        """Format AST as a full G-code program string."""
        return "\n".join(str(b) for b in self.blocks)
