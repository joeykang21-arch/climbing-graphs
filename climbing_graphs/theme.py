"""Shared look and output handling for every chart.

Charts are dark-themed and sized 16:9 for video. Series colours come from a
colour-blind-checked categorical palette and are always used in the same order.
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import plotly.graph_objects as go

WIDTH, HEIGHT = 1600, 900

SURFACE = "#1a1a19"
INK = "#f0efec"
INK_SECONDARY = "#c3c2b7"
INK_MUTED = "#898781"
GRID = "#2c2c2a"
AXIS = "#383835"

# Categorical slots, dark-surface steps. Slot 1 = default series, slot 2 = highlight / second series.
SERIES = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"]

FONT_FAMILY = 'system-ui, -apple-system, "Segoe UI", Arial, sans-serif'
BASE_FONT_SIZE = 18
MARGIN = dict(l=90, r=40, t=110, b=70)


def base_layout(title: str, subtitle: str | None = None, **overrides) -> dict:
    text = f"<b>{title}</b>"
    if subtitle:
        text += f"<br><span style='font-size:0.65em;color:{INK_SECONDARY}'>{subtitle}</span>"
    layout = dict(
        template="plotly_dark",
        title=dict(text=text, x=0.5, xanchor="center", font=dict(size=30, color=INK)),
        font=dict(family=FONT_FAMILY, size=BASE_FONT_SIZE, color=INK_SECONDARY),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        width=WIDTH,
        height=HEIGHT,
        margin=MARGIN,
        hoverlabel=dict(font=dict(family=FONT_FAMILY)),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    layout.update(overrides)
    return layout


def style_axes(fig: go.Figure) -> None:
    """Recessive hairline grid and axes."""
    fig.update_xaxes(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, tickfont_color=INK_MUTED)
    fig.update_yaxes(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS, tickfont_color=INK_MUTED)


def add_background_image(fig: go.Figure, image: Path) -> None:
    """Stretch a local image behind the plot. The image is embedded in the
    output, so the saved HTML is self-contained and portable."""
    mime = mimetypes.guess_type(image.name)[0] or "image/png"
    data_uri = f"data:{mime};base64,{base64.b64encode(image.read_bytes()).decode()}"
    fig.add_layout_image(
        source=data_uri, xref="paper", yref="paper", x=0, y=1, sizex=1, sizey=1,
        sizing="stretch", layer="below",
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)")


def save(fig: go.Figure, path: Path, *, show: bool = False) -> Path:
    """Write ``fig`` as standalone HTML (plotly.js loaded from CDN) and optionally open it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(path, include_plotlyjs="cdn", auto_play=False)
    if show:
        fig.show(renderer="browser")
    return path
