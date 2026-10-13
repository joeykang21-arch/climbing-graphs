"""Figure builders. Each function returns a ``plotly.graph_objects.Figure``."""

from .frontier import COMPARISONS, frontier_chart, gap_chart
from .strip import strip_chart
from .thumbnail import thumbnail_chart
from .timeline import timeline_chart

__all__ = [
    "COMPARISONS",
    "frontier_chart",
    "gap_chart",
    "strip_chart",
    "thumbnail_chart",
    "timeline_chart",
]
