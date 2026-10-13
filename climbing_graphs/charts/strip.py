"""One-dimensional "strip" chart: every climber is a dot at the height of their
score. The horizontal position is random jitter and carries no meaning."""

from __future__ import annotations

import math
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .. import theme
from ..labels import spread_labels

X_RANGE = (-0.45, 0.45)
JITTER = 0.05  # half-width of the strip, in x units
LABEL_X = 0.1  # labels sit in two columns this far either side of centre
LABEL_FONT_SIZE = 17
LABEL_LINE_PX = 23  # vertical room each label needs


def strip_chart(
    table: pd.DataFrame,
    *,
    title: str,
    subtitle: str,
    score_label: str,
    highlight: str | None = None,
    top_labels: int = 12,
    extra_labels: Iterable[str] = (),
    log_axis: bool = False,
    seed: int = 7,
    background: Path | None = None,
) -> go.Figure:
    """``table`` has columns ``climber``, ``score`` and ``detail`` (hover text),
    sorted best first."""
    table = table.reset_index(drop=True).copy()
    table["x"] = np.random.default_rng(seed).uniform(-JITTER, JITTER, len(table))
    is_highlight = table["climber"] == highlight

    # Alternate labels right / left by rank so neighbours separate, and move each
    # labelled dot to its label's half of the strip so leader lines don't cross it.
    labelled = _pick_labels(table, top_labels, [highlight, *extra_labels])
    sides = pd.Series([1 if k % 2 == 0 else -1 for k in range(len(labelled))], index=labelled)
    table.loc[labelled, "x"] = sides * table.loc[labelled, "x"].abs()

    fig = go.Figure()
    for rows, name, marker in [
        (table[~is_highlight], "Climbers", dict(size=12, color=theme.SERIES[0], opacity=0.85)),
        (table[is_highlight], highlight, dict(size=20, color=theme.SERIES[1], symbol="diamond")),
    ]:
        if rows.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=rows["x"],
                y=rows["score"],
                mode="markers",
                name=name,
                marker=dict(line=dict(width=1.5, color=theme.SURFACE), **marker),
                customdata=rows[["climber", "detail"]],
                hovertemplate=f"<b>%{{customdata[0]}}</b><br>{score_label}: %{{y:.3~f}}"
                "<br>%{customdata[1]}<extra></extra>",
            )
        )

    y_range = _axis_range(table["score"], log_axis)
    to_axis = math.log10 if log_axis else float
    for annotation in _label_annotations(table.loc[labelled], sides, highlight, y_range, to_axis):
        fig.add_annotation(annotation)

    fig.update_layout(
        theme.base_layout(title, subtitle),
        xaxis=dict(range=X_RANGE, visible=False),
        yaxis=dict(
            title=score_label,
            type="log" if log_axis else "linear",
            range=y_range,
            showgrid=False,
            showline=True,
            linewidth=2,
            tickfont=dict(size=22),
            **(_log_ticks(y_range) if log_axis else {}),
        ),
        legend=dict(x=1, xanchor="right", y=1, yanchor="top"),
    )
    theme.style_axes(fig)
    if background is not None:
        theme.add_background_image(fig, background)
    return fig


def _axis_range(scores: pd.Series, log_axis: bool) -> list[float]:
    """Explicit range in axis units (log10 units for a log axis)."""
    if log_axis:
        low, high = math.log10(scores.min()), math.log10(scores.max())
        pad = max(0.05 * (high - low), 0.1)
        return [low - pad, high + pad]
    return [0, scores.max() * 1.06]


def _log_ticks(y_range: list[float]) -> dict:
    """1-2-5 ticks instead of plotly's cluttered minor labels."""
    low, high = 10 ** y_range[0], 10 ** y_range[1]
    ticks = [m * 10**e for e in range(math.floor(y_range[0]), math.ceil(y_range[1]) + 1) for m in (1, 2, 5)]
    return dict(tickmode="array", tickvals=[t for t in ticks if low <= t <= high])


def _pick_labels(table: pd.DataFrame, top: int, always: list[str | None]) -> list[int]:
    chosen = list(table.index[:top])
    chosen += [i for i in table.index[table["climber"].isin([n for n in always if n])] if i not in chosen]
    return chosen


def _label_annotations(labelled: pd.DataFrame, sides: pd.Series, highlight, y_range, to_axis) -> list[dict]:
    plot_height = theme.HEIGHT - theme.MARGIN["t"] - theme.MARGIN["b"]
    min_gap = LABEL_LINE_PX / plot_height * (y_range[1] - y_range[0])

    annotations = []
    for side in (1, -1):
        rows = labelled[sides == side]
        targets = [to_axis(s) for s in rows["score"]]
        positions = spread_labels(targets, min_gap, *y_range)
        for (_, row), target, position in zip(rows.iterrows(), targets, positions):
            is_highlight = row["climber"] == highlight
            annotations.append(
                dict(
                    x=row["x"],
                    y=target,
                    ax=side * LABEL_X,
                    ay=position,
                    axref="x",
                    ayref="y",
                    text=f"<b>{row['climber']}</b>" if is_highlight else row["climber"],
                    xanchor="left" if side == 1 else "right",
                    font=dict(size=LABEL_FONT_SIZE + (4 if is_highlight else 0), color=theme.INK),
                    showarrow=True,
                    arrowhead=0,
                    arrowwidth=1,
                    arrowcolor=theme.INK_MUTED,
                    standoff=7,
                )
            )
    return annotations
