"""Video thumbnail.

NOTE: this is an *illustrative* mock-up for a thumbnail, not real data. The
scores below are hand-picked for composition; use the ``best`` charts for
actual rankings.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from .. import theme

HIGHLIGHT = ("Adam Ondra", 0.18, 110)  # name, x, y

# name: (x, y). Hand-placed so the labels read well at thumbnail size.
NAMED = {
    "Vadim Timonov": (-0.44, 17),
    "Jules Marchaland": (-0.22, 20),
    "Noah Wheeler": (-0.13, 7),
    "Jakob Schubert": (-0.08, 19),
    "Tomoa Narasaki": (-0.05, 10),
    "Nicolai Uznik": (0.12, 12),
    "Jimmy Webb": (0.40, 21),
    "Daniel Woods": (0.42, 15),
    "Aidan Roberts": (0.46, 13),
    "Yannick Flohé": (0.49, 19),
    "Will Bosi": (0.54, 28),
}

CROWD_SIZE = 85
CROWD_ROWS = 3
CROWD_Y = (1, 6)


def thumbnail_chart(seed: int = 7) -> go.Figure:
    rng = np.random.default_rng(seed)
    crowd_x = np.linspace(-0.46, 0.56, CROWD_SIZE) + rng.uniform(-0.008, 0.008, CROWD_SIZE)
    crowd_y = rng.integers(CROWD_Y[0], CROWD_Y[1] + 1, CROWD_SIZE) + (np.arange(CROWD_SIZE) % CROWD_ROWS) * 0.15

    names = list(NAMED)
    xs = [NAMED[n][0] for n in names]
    fig = go.Figure(
        [
            go.Scatter(x=crowd_x, y=crowd_y, mode="markers", marker=dict(size=9, color=theme.SERIES[0])),
            go.Scatter(
                x=xs,
                y=[NAMED[n][1] for n in names],
                mode="markers+text",
                text=names,
                textposition=["middle right" if x <= 0 else "middle left" for x in xs],
                textfont=dict(size=16, color="white"),
                marker=dict(size=9, color=theme.SERIES[0]),
            ),
            go.Scatter(
                x=[HIGHLIGHT[1]],
                y=[HIGHLIGHT[2]],
                mode="markers+text",
                text=[HIGHLIGHT[0]],
                textposition="middle right",
                textfont=dict(size=22, color="white"),
                marker=dict(size=16, symbol="diamond", color=theme.SERIES[1]),
            ),
        ]
    )
    fig.update_layout(
        template="plotly_dark",
        width=1728,
        height=972,
        showlegend=False,
        paper_bgcolor="black",
        plot_bgcolor="black",
        margin=dict(l=80, r=30, t=30, b=40),
        xaxis=dict(visible=False, range=[-0.5, 0.58]),
        yaxis=dict(showgrid=False, zeroline=False, showline=True, linewidth=3, linecolor="white",
                   tickfont=dict(size=18, color="white"), range=[0, 115]),
    )
    return fig
