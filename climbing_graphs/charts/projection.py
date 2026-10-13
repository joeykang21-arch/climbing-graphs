"""'When will grade X be reached?' charts."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import plotly.graph_objects as go

from .. import theme
from ..dates import decimal_year
from ..frontier import drop_superseded
from ..grades import FRENCH_SPORT, V_BOULDER, GradeScale
from ..labels import spread_labels
from ..milestones import (
    BOULDER_FLASH_MEN,
    BOULDER_MEN,
    FREE_SOLO,
    SPORT_FLASH_ONSIGHT_MEN,
    SPORT_REDPOINT_MEN,
    Milestone,
)
from ..projections import MODELS, project

_DASHES = {"direct": "dash", "linear_gap": "dot", "exp_gap": "longdash"}


@dataclass(frozen=True)
class ProjectionSpec:
    key: str
    title: str
    scale: GradeScale
    milestones: Sequence[Milestone]
    target: str
    from_grade: str | None = None  # ignore milestones below this grade
    point_name: str = "Actual first ascent"
    axis_title: str = "Grade"
    reveal: Milestone | None = None  # a known result held out of the fit, shown for comparison


PROJECTIONS: dict[str, ProjectionSpec] = {
    p.key: p
    for p in [
        ProjectionSpec(
            "boulder-flash-v16",
            "When Will the First V16 Boulder Be Flashed?",
            V_BOULDER,
            BOULDER_FLASH_MEN,
            target="V16",
            point_name="Actual first flash",
            axis_title="Flash grade",
        ),
        ProjectionSpec(
            "boulder-v19",
            "When Will the First V19 Boulder Be Climbed?",
            V_BOULDER,
            BOULDER_MEN,
            target="V19",
            from_grade="V13",
            axis_title="Boulder grade",
        ),
        ProjectionSpec(
            "sport-9c-hindcast",
            "When Was 9c Expected to Arrive?",
            FRENCH_SPORT,
            [m for m in SPORT_REDPOINT_MEN if m.grade != "9c"],
            target="9c",
            point_name="Actual first redpoint",
            axis_title="Sport grade",
            reveal=next(m for m in SPORT_REDPOINT_MEN if m.grade == "9c"),
        ),
        ProjectionSpec(
            "sport-9c-plus",
            "When Will the First 9c+ Be Redpointed?",
            FRENCH_SPORT,
            SPORT_REDPOINT_MEN,
            target="9c+",
            point_name="Actual first redpoint",
            axis_title="Sport grade",
        ),
        ProjectionSpec(
            "sport-9c-plus-recent",
            "When Will the First 9c+ Be Redpointed? (since 9a+)",
            FRENCH_SPORT,
            SPORT_REDPOINT_MEN,
            target="9c+",
            from_grade="9a+",
            point_name="Actual first redpoint",
            axis_title="Sport grade",
        ),
        ProjectionSpec(
            "flash-9b",
            "When Will the First 9b Be Flashed or Onsighted?",
            FRENCH_SPORT,
            SPORT_FLASH_ONSIGHT_MEN,
            target="9b",
            point_name="Actual first flash/onsight",
            axis_title="Sport grade",
        ),
        ProjectionSpec(
            "free-solo-8c-plus",
            "When Will the First 8c+ Free Solo Happen?",
            FRENCH_SPORT,
            FREE_SOLO,
            target="8c+",
            point_name="Actual first free solo",
            axis_title="Route grade",
        ),
    ]
}


def projection_chart(spec: ProjectionSpec) -> go.Figure:
    scale = spec.scale
    floor = scale.position(spec.from_grade) if spec.from_grade else -np.inf
    known = drop_superseded([m for m in spec.milestones if scale.position(m.grade) >= floor], scale)
    positions = np.array([scale.position(m.grade) for m in known])
    years = np.array([decimal_year(m.when) for m in known])
    target = scale.position(spec.target)
    projection = project(positions, years, target)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=positions,
            y=years,
            mode="markers+text",
            name=spec.point_name,
            marker=dict(size=13, color=theme.INK, line=dict(width=2, color=theme.SURFACE)),
            text=[_point_label(m, scale) for m in known],
            # Alternate above-left / below-right of the rising curve so labels don't collide.
            textposition=["top left" if i % 2 else "bottom right" for i in range(len(known))],
            textfont=dict(color=theme.INK_SECONDARY, size=14),
            customdata=[m.climb or "" for m in known],
            hovertemplate="%{text}<br>%{customdata}<extra></extra>",
        )
    )

    target_label = scale.label(spec.target)
    for i, (model, name) in enumerate(MODELS.items()):
        predicted = projection.at_target(model)
        fig.add_trace(
            go.Scatter(
                x=projection.positions,
                y=projection.years[model],
                mode="lines+markers",
                name=f"{name} ({target_label} ≈ {predicted:.1f})",
                line=dict(width=3, dash=_DASHES[model], color=theme.SERIES[i]),
                marker=dict(size=8),
                hovertemplate=f"{name}<br>%{{y:.1f}}<extra></extra>",
            )
        )

    if spec.reveal is not None:
        fig.add_trace(
            go.Scatter(
                x=[scale.position(spec.reveal.grade)],
                y=[decimal_year(spec.reveal.when)],
                mode="markers+text",
                name=f"What actually happened ({spec.reveal.climb})",
                marker=dict(size=18, symbol="star", color=theme.SERIES[3]),
                text=[_point_label(spec.reveal, scale)],
                textposition="middle left",
                textfont=dict(color=theme.INK),
                hovertemplate="%{text}<extra></extra>",
            )
        )

    all_positions = projection.positions
    all_years = np.concatenate([years, *projection.years.values()])
    y_range = [np.floor(all_years.min()) - 2, np.ceil(all_years.max()) + 2]

    # Callouts with each model's target year, to the right of the target and spread apart.
    predictions = [projection.at_target(model) for model in MODELS]
    plot_height = theme.HEIGHT - theme.MARGIN["t"] - theme.MARGIN["b"]
    min_gap = 34 / plot_height * (y_range[1] - y_range[0])
    for i, (predicted, label_y) in enumerate(zip(predictions, spread_labels(predictions, min_gap, *y_range))):
        fig.add_annotation(
            x=target, y=predicted, ax=target + 0.35, ay=label_y, axref="x", ayref="y",
            text=f"{predicted:.1f}", xanchor="left", showarrow=True, arrowhead=0,
            arrowcolor=theme.SERIES[i], bgcolor="rgba(0,0,0,0.7)", bordercolor=theme.SERIES[i],
            font=dict(color=theme.INK),
        )
    fig.update_layout(
        theme.base_layout(spec.title),
        xaxis=dict(
            title=spec.axis_title,
            tickmode="array",
            tickvals=list(all_positions),
            ticktext=[scale.label_at(p) for p in all_positions],
            range=[all_positions[0] - 0.5, all_positions[-1] + 1.2],
        ),
        yaxis=dict(title="Year", range=y_range),
        legend=dict(title="Projection model", x=0.01, y=0.99),
    )
    theme.style_axes(fig)
    return fig


def _point_label(m: Milestone, scale: GradeScale) -> str:
    has_month = (m.when.month, m.when.day) != (1, 1)
    when = m.when.strftime("%b %Y") if has_month else str(m.when.year)
    return f"{when}<br>{scale.label(m.grade)}"
