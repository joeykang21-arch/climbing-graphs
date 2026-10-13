"""The "frontier": the hardest grade achieved so far, year by year."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from .grades import GradeScale
from .milestones import Milestone


def frontier_advances(milestones: Sequence[Milestone], scale: GradeScale) -> pd.DataFrame:
    """Milestones that raised the frontier (one row per year, hardest grade that
    year). Columns: ``year``, ``position``, ``grade``."""
    df = pd.DataFrame(
        {
            "year": [m.when.year for m in milestones],
            "position": [scale.position(m.grade) for m in milestones],
            "grade": [scale.label(m.grade) for m in milestones],
        }
    )
    best_per_year = df.sort_values("position").groupby("year").tail(1).sort_values("year")
    is_new_high = best_per_year["position"] > best_per_year["position"].cummax().shift(fill_value=float("-inf"))
    return best_per_year[is_new_high].reset_index(drop=True)


def drop_superseded(milestones: Sequence[Milestone], scale: GradeScale) -> list[Milestone]:
    """Drop milestones beaten by a strictly earlier ascent of a harder grade, and
    sort the rest by grade.

    For example, if 7a+ was free soloed in 1961, a first 7a solo in 1978 is not a
    frontier advance and would otherwise give the projections a negative gap.
    """
    kept = [
        m for m in milestones
        if not any(o.when < m.when and scale.position(o.grade) > scale.position(m.grade) for o in milestones)
    ]
    return sorted(kept, key=lambda m: scale.position(m.grade))


def frontier_by_year(
    milestones: Sequence[Milestone], scale: GradeScale, years: range
) -> pd.Series:
    """Hardest grade position achieved by the end of each year in ``years``
    (NaN before the first milestone)."""
    advances = frontier_advances(milestones, scale).set_index("year")["position"]
    return advances.reindex(years).cummax().ffill().rename_axis("year")


def frontier_gap(
    leader: Sequence[Milestone], follower: Sequence[Milestone], scale: GradeScale, years: range
) -> pd.Series:
    """Grades between two frontiers, for years where both exist."""
    gap = frontier_by_year(leader, scale, years) - frontier_by_year(follower, scale, years)
    return gap.dropna()
