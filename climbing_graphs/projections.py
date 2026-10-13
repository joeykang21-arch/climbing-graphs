"""Projecting when the next grade will be reached.

Three simple models, all fitted to (grade position, decimal year) points:

``direct``      year is a straight line in grade.
``linear_gap``  the wait between consecutive grades grows linearly.
``exp_gap``     the wait between consecutive grades grows exponentially.

The gap models work per grade *step*, so a missing grade in the data (e.g. no
known 8a+ flash) is spread over the steps it spans instead of being treated
as a single step.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MODELS = {
    "direct": "Direct linear fit",
    "linear_gap": "Linear-gap model",
    "exp_gap": "Exponential-gap model",
}


@dataclass(frozen=True)
class Projection:
    positions: np.ndarray  # every grade position from the first known point to the target
    years: dict[str, np.ndarray]  # model key -> projected decimal year at each position

    def at_target(self, model: str) -> float:
        return float(self.years[model][-1])


def project(positions: np.ndarray, years: np.ndarray, target: float) -> Projection:
    """Fit all three models to the known points and run them out to ``target``."""
    positions = np.asarray(positions, dtype=float)
    years = np.asarray(years, dtype=float)
    if len(positions) < 3:
        raise ValueError("need at least three known points to fit the gap models")
    order = np.argsort(positions)
    positions, years = positions[order], years[order]

    start = positions[0]
    grid = np.arange(start, target + 1)
    steps_from_start = grid[1:] - start

    # Each observed gap is spread evenly over the grade steps it covers and
    # indexed by the step at which it ends.
    gap_per_step = np.diff(years) / np.diff(positions)
    gap_end_step = positions[1:] - start

    linear = np.poly1d(np.polyfit(gap_end_step, gap_per_step, 1))

    # log() needs positive gaps; non-monotonic data (e.g. free solos) can have
    # negative ones, so shift them positive for the fit and back afterwards.
    shift = 0.0 if gap_per_step.min() > 0 else 0.25 - gap_per_step.min()
    log_fit = np.polyfit(gap_end_step, np.log(gap_per_step + shift), 1)

    def exponential(step):
        return np.exp(np.polyval(log_fit, step)) - shift

    return Projection(
        positions=grid,
        years={
            "direct": np.polyval(np.polyfit(positions, years, 1), grid),
            "linear_gap": years[0] + np.concatenate([[0], np.cumsum(linear(steps_from_start))]),
            "exp_gap": years[0] + np.concatenate([[0], np.cumsum(exponential(steps_from_start))]),
        },
    )
