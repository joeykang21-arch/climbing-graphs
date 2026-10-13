"""Frontier charts: hardest grade over time for two groups, and the gap between them."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

import plotly.graph_objects as go

from .. import theme
from ..frontier import frontier_advances, frontier_by_year, frontier_gap
from ..grades import FRENCH_SPORT, V_BOULDER, GradeScale
from ..milestones import (
    BOULDER_FLASH_MEN,
    BOULDER_MEN,
    BOULDER_WOMEN,
    SPORT_FLASH_ONSIGHT_MEN,
    SPORT_FLASH_ONSIGHT_WOMEN,
    SPORT_REDPOINT_MEN,
    SPORT_REDPOINT_WOMEN,
    Milestone,
)

END_YEAR = date.today().year


@dataclass(frozen=True)
class Comparison:
    key: str
    title: str
    scale: GradeScale
    leader: tuple[str, Sequence[Milestone]]  # (legend name, milestones); the gap is leader - follower
    follower: tuple[str, Sequence[Milestone]]
    legend_title: str


COMPARISONS: dict[str, Comparison] = {
    c.key: c
    for c in [
        Comparison(
            "sport-gender",
            "Highest Sport Grade Redpointed by Men vs Women",
            FRENCH_SPORT,
            ("Men", SPORT_REDPOINT_MEN),
            ("Women", SPORT_REDPOINT_WOMEN),
            "Category",
        ),
        Comparison(
            "boulder-gender",
            "Highest Boulder Grade Climbed by Men vs Women",
            V_BOULDER,
            ("Men", BOULDER_MEN),
            ("Women", BOULDER_WOMEN),
            "Category",
        ),
        Comparison(
            "flash-gender",
            "Highest Sport Flash/Onsight Grade by Men vs Women",
            FRENCH_SPORT,
            ("Men", SPORT_FLASH_ONSIGHT_MEN),
            ("Women", SPORT_FLASH_ONSIGHT_WOMEN),
            "Category",
        ),
        Comparison(
            "sport-style",
            "Hardest Sport Redpoint vs Flash/Onsight",
            FRENCH_SPORT,
            ("Redpoint", SPORT_REDPOINT_MEN),
            ("Flash / Onsight", SPORT_FLASH_ONSIGHT_MEN),
            "Style",
        ),
        Comparison(
            "boulder-style",
            "Hardest Boulder Climbed vs Flashed",
            V_BOULDER,
            ("All ascents", BOULDER_MEN),
            ("Flash", BOULDER_FLASH_MEN),
            "Style",
        ),
    ]
}


def frontier_chart(comparison: Comparison, end_year: int = END_YEAR) -> go.Figure:
    scale = comparison.scale
    groups = [comparison.leader, comparison.follower]
    first_year = min(m.when.year for _, milestones in groups for m in milestones)
    years = range(first_year, end_year + 1)

    fig = go.Figure()
    for i, ((name, milestones), text_position) in enumerate(zip(groups, ["top left", "bottom right"])):
        color = theme.SERIES[i]
        line = frontier_by_year(milestones, scale, years).dropna()
        advances = frontier_advances(milestones, scale)
        fig.add_trace(
            go.Scatter(
                x=list(line.index),
                y=line.to_numpy(),
                mode="lines",
                line=dict(width=4, color=color, shape="hv"),
                name=name,
                legendgroup=name,
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=advances["year"],
                y=advances["position"],
                mode="markers+text",
                marker=dict(size=10, color=color, line=dict(width=2, color=theme.SURFACE)),
                text=advances["grade"],
                textposition=text_position,
                textfont=dict(color=theme.INK),
                name=name,
                legendgroup=name,
                showlegend=False,
                cliponaxis=False,
                hovertemplate=f"<b>{name}</b><br>%{{text}} in %{{x}}<extra></extra>",
            )
        )

    used = [m.grade for _, milestones in groups for m in milestones]
    tickvals, ticktext = scale.ticks(used)
    fig.update_layout(
        theme.base_layout(f"{comparison.title} Over Time"),
        xaxis=dict(title="Year", range=[first_year - 2, end_year + 2]),
        yaxis=dict(
            title="Highest grade achieved",
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,
            range=[tickvals[0] - 0.7, tickvals[-1] + 0.7],
        ),
        legend=dict(title=comparison.legend_title, x=0.01, y=0.99),
    )
    theme.style_axes(fig)
    return fig


def gap_chart(comparison: Comparison, end_year: int = END_YEAR) -> go.Figure:
    leader_name, leader = comparison.leader
    follower_name, follower = comparison.follower
    first_year = min(m.when.year for m in [*leader, *follower])
    gap = frontier_gap(leader, follower, comparison.scale, range(first_year, end_year + 1))

    # Label the gap only where it changes, so the chart isn't covered in numbers.
    changes = gap[gap.diff() != 0]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(gap.index),
            y=gap.to_numpy(),
            mode="lines",
            line=dict(width=4, color=theme.SERIES[0], shape="hv"),
            fill="tozeroy",
            name="Gap",
            hovertemplate="%{x}: %{y:g} grades<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=list(changes.index),
            y=changes.to_numpy(),
            mode="markers+text",
            marker=dict(size=9, color=theme.SERIES[0], line=dict(width=2, color=theme.SURFACE)),
            text=[f"{v:g}" for v in changes],
            textposition="top center",
            textfont=dict(color=theme.INK),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        theme.base_layout(
            f"Gap: {comparison.title}",
            f"{leader_name} frontier minus {follower_name.lower()} frontier, in grades",
        ),
        xaxis=dict(title="Year", range=[gap.index.min() - 1, end_year + 1]),
        yaxis=dict(title="Gap (grades)", range=[0, gap.max() + 1], dtick=0.5 if (gap % 1).any() else 1),
        showlegend=False,
    )
    theme.style_axes(fig)
    return fig
