"""Grade scales and grade-string normalization.

Scraped grades arrive in inconsistent forms ("8B +", "8b+", "8B +",
"8Bplus"). ``normalize_grade`` turns all of them into one canonical key, and a
``GradeScale`` orders those keys so grades can be compared and plotted.

Split grades such as ``"9a/9a+"``, ``"8a/+"`` or ``"V10/11"`` sit halfway
between their two neighbours.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

_WHITESPACE = re.compile(r"\s+")  # unicode-aware: also matches nbsp / thin spaces
_LEADING_LETTERS = re.compile(r"^[A-Z]*")


def normalize_grade(raw: object) -> str | None:
    """Return an uppercase, whitespace-free grade key, or None if empty/missing."""
    if raw is None or (not isinstance(raw, str) and pd.isna(raw)):
        return None
    key = _WHITESPACE.sub("", str(raw)).upper().replace("PLUS", "+")
    return key or None


@dataclass(frozen=True)
class GradeScale:
    """An ordered grade scale, easiest first.

    ``lowercase`` controls how labels are displayed (French sport grades are
    written "9a+", Font and V grades "8C+" / "V16").
    """

    name: str
    grades: tuple[str, ...]
    lowercase: bool = False
    _positions: dict[str, int] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_positions", {g.upper(): i for i, g in enumerate(self.grades)})

    def __contains__(self, grade: object) -> bool:
        try:
            self.position(grade)
        except (KeyError, TypeError):
            return False
        return True

    def position(self, grade: object) -> float:
        """Numeric position on the scale (one step per grade)."""
        key = normalize_grade(grade)
        if key is None:
            raise TypeError("grade is empty")
        if key in self._positions:
            return float(self._positions[key])
        if "/" in key:
            low, high = key.split("/", 1)
            high = _expand_split_upper(low, high)
            if low in self._positions and high in self._positions:
                return (self._positions[low] + self._positions[high]) / 2
        raise KeyError(f"{grade!r} is not on the {self.name} scale")

    def label(self, grade: object) -> str:
        """Display label for a grade, e.g. ``"9B+"`` -> ``"9b+"`` on the sport scale."""
        key = normalize_grade(grade)
        if key is None:
            raise TypeError("grade is empty")
        return key.lower() if self.lowercase else key

    def label_at(self, position: float) -> str:
        """Inverse of ``position`` for whole-grade positions."""
        return self.label(self.grades[int(position)])

    def ticks(self, used: list[str] | tuple[str, ...]) -> tuple[list[float], list[str]]:
        """Tick positions/labels covering every whole grade between the extremes of
        ``used``, plus any split grades that actually appear in ``used``."""
        positions = {self.position(g): self.label(g) for g in used}
        low, high = int(min(positions)), int(max(positions) + 0.5)
        for i in range(low, high + 1):
            positions.setdefault(float(i), self.label(self.grades[i]))
        ordered = sorted(positions)
        return ordered, [positions[p] for p in ordered]


def _expand_split_upper(low: str, high: str) -> str:
    """Complete the abbreviated upper half of a split grade.

    "8A" + "+"   -> "8A+"   (8a/+)
    "V10" + "11" -> "V11"   (V10/11)
    "9A" + "9A+" -> "9A+"   (9a/9a+)
    """
    if high == "+":
        return low + "+"
    if high.isdigit():
        return _LEADING_LETTERS.match(low).group(0) + high
    return high


def _alternating(numbers: range, letters: str) -> tuple[str, ...]:
    return tuple(f"{n}{letter}{plus}" for n in numbers for letter in letters for plus in ("", "+"))


FRENCH_SPORT = GradeScale(
    "French sport", _alternating(range(5, 10), "abc"), lowercase=True
)
FONT_BOULDER = GradeScale("Font boulder", _alternating(range(5, 10), "ABC"))
V_BOULDER = GradeScale("V boulder", tuple(f"V{n}" for n in range(0, 21)))

# Consensus Font -> V conversion for the hard grades this project works with.
FONT_TO_V = {
    "7C+": "V10",
    "8A": "V11",
    "8A+": "V12",
    "8B": "V13",
    "8B+": "V14",
    "8C": "V15",
    "8C+": "V16",
    "9A": "V17",
    "9A+": "V18",
    "9B": "V19",
}


def font_with_v(grade: str) -> str:
    """``"8C+"`` -> ``"8C+ (V16)"``; grades without a known conversion pass through."""
    key = normalize_grade(grade)
    return f"{key} ({FONT_TO_V[key]})" if key in FONT_TO_V else str(key)
