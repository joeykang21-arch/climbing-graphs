"""Scoring systems for ranking climbers by their hardest ascents.

Each ascent earns points based on its grade; a climber's score is the sum over
their ascents. The schemes differ only in how many points each grade is worth:

``exponential`` (the main video): 18 / 5 / 1
    The three hardest grades in a list are worth 18, 5 and 1 points. Each
    grade step is estimated to be ~5x harder, which would give 25 / 5 / 1; the
    top grade is discounted from 25 to 18 because grades at the very limit are
    the least settled. The 5x figure is based on personal experience and is
    somewhat arbitrary; the other schemes show how sensitive rankings are to it.

``conservative``: 4 / 2 / 1
    Same idea with each grade step only doubling in value.

``rarity`` (ascent-count based):
    Points are inversely proportional to how many ascents of that grade exist,
    normalized so the easiest grade in the list is worth 1. With 259 8B, 40 8B+
    and 7 8C flashes, an 8C flash is worth 259 / 7 = 37 points. This lets the
    data set the exchange rate instead of a guess.

``equal``: every ascent is worth 1 (a plain count of hard ascents).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import pandas as pd

from .grades import FONT_BOULDER, FRENCH_SPORT, GradeScale

GradeWeights = dict[str, float]


def top_grade_weights(points: Sequence[float]) -> Callable[[pd.Series, GradeScale], GradeWeights]:
    """Award ``points[0]`` for the hardest grade present, ``points[1]`` for the
    next hardest, and so on. Grades below the last entry are worth 0."""

    def weigh(grades: pd.Series, scale: GradeScale) -> GradeWeights:
        hardest_first = sorted(grades.unique(), key=scale.position, reverse=True)
        return {g: float(points[i]) if i < len(points) else 0.0 for i, g in enumerate(hardest_first)}

    return weigh


def rarity_weights(grades: pd.Series, scale: GradeScale) -> GradeWeights:
    """Points = ascents of the easiest grade / ascents of this grade."""
    counts = grades.value_counts()
    baseline = counts[min(counts.index, key=scale.position)]
    return {g: baseline / n for g, n in counts.items()}


def equal_weights(grades: pd.Series, scale: GradeScale) -> GradeWeights:
    return {g: 1.0 for g in grades.unique()}


@dataclass(frozen=True)
class Scheme:
    key: str
    title: str
    weigh: Callable[[pd.Series, GradeScale], GradeWeights]
    log_axis: bool = False  # rarity scores span orders of magnitude


SCHEMES: dict[str, Scheme] = {
    s.key: s
    for s in [
        Scheme("exponential", "18 / 5 / 1 points", top_grade_weights([18, 5, 1])),
        Scheme("conservative", "4 / 2 / 1 points", top_grade_weights([4, 2, 1])),
        Scheme("rarity", "points by rarity of grade", rarity_weights, log_axis=True),
        Scheme("equal", "1 point per ascent", equal_weights),
    ]
}


@dataclass(frozen=True)
class Category:
    """One ranked list: where the ascents come from and how to present them."""

    key: str
    title: str
    url: str
    scale: GradeScale
    score_label: str
    highlight: str | None = None
    always_label: tuple[str, ...] = ()


_CLIMBING_HISTORY = "https://climbing-history.org/list/"

CATEGORIES: dict[str, Category] = {
    c.key: c
    for c in [
        Category(
            "flashes",
            "Best Boulder Flashers",
            _CLIMBING_HISTORY + "20/hard-boulder-problem-flashes",
            FONT_BOULDER,
            "Flash score",
            highlight="Adam Ondra",
        ),
        Category(
            "boulder",
            "Best Hard Boulderers",
            _CLIMBING_HISTORY + "14/hard-boulder-problem-ascents",
            FONT_BOULDER,
            "Ascent score",
            highlight="Will Bosi",
        ),
        Category(
            "sport",
            "Best Hard Sport Climbers",
            _CLIMBING_HISTORY + "5/hard-sport-climbing-ascents",
            FRENCH_SPORT,
            "Sport score",
            highlight="Adam Ondra",
            always_label=("Will Bosi",),
        ),
        Category(
            "onsights",
            "Best Onsighters",
            _CLIMBING_HISTORY + "37/hard-sport-climbing-onsights",
            FRENCH_SPORT,
            "Onsight score",
            highlight="Adam Ondra",
        ),
    ]
}


@dataclass(frozen=True)
class Ranking:
    table: pd.DataFrame  # climber, score, detail; sorted best first
    weights: GradeWeights  # hardest grade first


def score_climbers(ascents: pd.DataFrame, scheme: Scheme, scale: GradeScale) -> Ranking:
    """Rank climbers in ``ascents`` (columns ``climber``, ``grade``) under ``scheme``.

    Grades that are not on ``scale`` are ignored. Climbers whose total is 0
    (only ascents of grades the scheme doesn't reward) are dropped.
    """
    ascents = ascents[ascents["grade"].map(lambda g: g in scale)]
    weights = scheme.weigh(ascents["grade"], scale)
    weights = dict(sorted(weights.items(), key=lambda kv: scale.position(kv[0]), reverse=True))

    counts = pd.crosstab(ascents["climber"], ascents["grade"])[list(weights)]
    table = pd.DataFrame(
        {
            "climber": counts.index,
            "score": counts.mul(pd.Series(weights)).sum(axis=1).to_numpy(),
            "detail": [_describe_counts(row, scale) for _, row in counts.iterrows()],
        }
    )
    table = table[table["score"] > 0]
    table = table.sort_values(["score", "climber"], ascending=[False, True], ignore_index=True)
    return Ranking(table, weights)


def describe_weights(weights: GradeWeights, scale: GradeScale) -> str:
    """``"8C = 18 · 8B+ = 5 · 8B = 1"``"""
    return " · ".join(f"{scale.label(g)} = {w:.3g}" for g, w in weights.items())


def _describe_counts(row: pd.Series, scale: GradeScale) -> str:
    return "<br>".join(f"{scale.label(g)}: {int(n)}" for g, n in row.items() if n)
