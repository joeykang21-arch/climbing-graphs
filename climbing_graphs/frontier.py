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
