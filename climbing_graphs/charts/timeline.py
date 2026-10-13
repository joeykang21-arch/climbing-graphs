"""Animated, month-by-month build-up of every hard boulder ascent."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .. import theme
from ..grades import FONT_BOULDER, font_with_v

GRADES = ["8C+", "9A", "9A+"]  # easiest first
SIZES = {"8C+": 8, "9A": 12, "9A+": 16}
FRAME_MS = 450


def timeline_chart(ascents: pd.DataFrame) -> go.Figure:
    """``ascents``: output of ``sources.read_ascent_list`` for the hard boulder list.
    Ascents with unparseable dates or other grades are left out."""
    df = ascents[ascents["grade"].isin(GRADES)].dropna(subset=["date"]).sort_values("date")
    df = df.assign(
        y=df["grade"].map(FONT_BOULDER.position),
        month=df["date"].dt.to_period("M").dt.to_timestamp(),
        number=range(1, len(df) + 1),
    )
    months = sorted(df["month"].unique())
    labels = [pd.Timestamp(m).strftime("%Y-%m") for m in months]

    def traces(up_to) -> list[go.Scatter]:
        shown = df[df["month"] <= up_to]
        return [_grade_trace(shown[shown["grade"] == g], g, i) for i, g in enumerate(GRADES)]

    play = dict(frame=dict(duration=FRAME_MS, redraw=True), transition=dict(duration=0), fromcurrent=True)
    pause = dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))
    jump = dict(frame=dict(duration=0, redraw=True), mode="immediate", transition=dict(duration=0))

    fig = go.Figure(
        data=traces(months[-1]),
        frames=[go.Frame(name=label, data=traces(m)) for m, label in zip(months, labels)],
    )
    fig.update_layout(
        theme.base_layout("The Hardest Boulder Problem Ascents Ever"),
        xaxis=dict(title="Date", range=[df["date"].min() - pd.Timedelta(days=365), df["date"].max() + pd.Timedelta(days=180)]),
        yaxis=dict(
            title="Grade",
            tickmode="array",
            tickvals=[FONT_BOULDER.position(g) for g in GRADES],
            ticktext=[font_with_v(g) for g in GRADES],
            range=[FONT_BOULDER.position(GRADES[0]) - 0.4, FONT_BOULDER.position(GRADES[-1]) + 0.4],
        ),
        legend=dict(title="Grade", x=0.01, y=0.99),
        margin=dict(theme.MARGIN, b=150),
        updatemenus=[
            dict(
                type="buttons", showactive=False, x=0, y=-0.12, xanchor="left", yanchor="top",
                buttons=[
                    dict(label="Play", method="animate", args=[None, play]),
                    dict(label="Pause", method="animate", args=[[None], pause]),
                ],
            )
        ],
        sliders=[
            dict(
                active=len(months) - 1, x=0.08, y=-0.12, len=0.92,
                currentvalue=dict(prefix="Month: "),
                steps=[dict(method="animate", label=label, args=[[label], jump]) for label in labels],
            )
        ],
    )
    theme.style_axes(fig)

    first = df.iloc[0]
    fig.add_annotation(
        x=first["date"], y=first["y"], ax=120, ay=-40,
        text=f"<b>First: {first['climber']}</b><br>{first['climb']}<br>{first['date_text']}",
        showarrow=True, arrowcolor=theme.INK_MUTED, bgcolor="rgba(0,0,0,0.7)",
        bordercolor=theme.SERIES[0], font=dict(color=theme.INK, size=14), align="left",
    )
    return fig


def _grade_trace(rows: pd.DataFrame, grade: str, slot: int) -> go.Scatter:
    return go.Scatter(
        x=rows["date"],
        y=rows["y"],
        mode="markers",
        name=font_with_v(grade),
        marker=dict(size=SIZES[grade], color=theme.SERIES[slot], opacity=0.9,
                    line=dict(width=1, color=theme.SURFACE)),
        customdata=rows[["climber", "climb", "date_text", "number"]],
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{customdata[2]}"
        "<br>Ascent #%{customdata[3]}<extra></extra>",
    )
