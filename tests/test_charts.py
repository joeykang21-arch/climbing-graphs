"""Smoke tests: every chart builds from offline data and saves to HTML."""

import pandas as pd
import pytest

from climbing_graphs import charts, theme
from climbing_graphs.cli import main


@pytest.mark.parametrize("key", list(charts.COMPARISONS))
def test_frontier_and_gap_charts(key):
    assert charts.frontier_chart(charts.COMPARISONS[key]).data
    assert charts.gap_chart(charts.COMPARISONS[key]).data


@pytest.mark.parametrize("key", list(charts.PROJECTIONS))
def test_projection_charts(key):
    fig = charts.projection_chart(charts.PROJECTIONS[key])
    assert len(fig.layout.annotations) == 3  # one target-year callout per model


@pytest.mark.parametrize("log_axis", [False, True])
def test_strip_chart_labels_top_climbers_and_highlight(log_axis):
    table = pd.DataFrame(
        {"climber": list("ABCDEFG"), "score": [40, 30, 30, 10, 5, 2, 1], "detail": [""] * 7}
    )
    fig = charts.strip_chart(
        table, title="t", subtitle="s", score_label="Score", highlight="F", top_labels=3, log_axis=log_axis
    )
    labelled = {a.text.replace("<b>", "").replace("</b>", "") for a in fig.layout.annotations}
    assert labelled == {"A", "B", "C", "F"}
    assert [t.name for t in fig.data] == ["Climbers", "F"]


def test_timeline_chart():
    ascents = pd.DataFrame(
        {
            "climber": ["X", "Y", "Z"],
            "climb": ["a", "b", "c"],
            "grade": ["8C+", "9A", "9A+"],
            "date_text": ["2008", "Oct 2016", "Nov 2025"],
            "date": pd.to_datetime(["2008-01-01", "2016-10-01", "2025-11-01"]),
        }
    )
    fig = charts.timeline_chart(ascents)
    assert len(fig.frames) == 3


def test_save_writes_small_html(tmp_path):
    path = theme.save(charts.thumbnail_chart(), tmp_path / "thumb.html")
    assert path.exists()
    assert path.stat().st_size < 200_000  # plotly.js comes from the CDN, not inlined


def test_cli_offline_commands(tmp_path):
    assert main(["frontier", "all", "--out", str(tmp_path)]) == 0
    assert main(["projection", "boulder-v19", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "gap_sport-gender.html").exists()
    assert (tmp_path / "projection_boulder-v19.html").exists()
