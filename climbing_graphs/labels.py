"""Automatic label placement for one-dimensional layouts.

The original notebooks nudged individual climbers' labels by hand, which broke
whenever the data changed. ``spread_labels`` instead moves labels vertically
just enough that no two are closer than ``min_gap``, keeping each group of
labels centred on the points it describes.
"""

from __future__ import annotations

from collections.abc import Sequence


def spread_labels(
    targets: Sequence[float], min_gap: float, lower: float | None = None, upper: float | None = None
) -> list[float]:
    """Return label positions, in the same order as ``targets``.

    Labels that would overlap are merged into blocks spaced exactly ``min_gap``
    apart; each block is centred on the mean of its targets (the least-squares
    placement). Blocks are then shifted to stay within ``[lower, upper]``.
    """
    order = sorted(range(len(targets)), key=lambda i: targets[i])
    blocks: list[list[int]] = []  # each block: indices into ``order``, ascending

    def block_start(block: list[int]) -> float:
        mean = sum(targets[order[k]] for k in block) / len(block)
        return mean - (len(block) - 1) * min_gap / 2

    for k in range(len(order)):
        blocks.append([k])
        while len(blocks) > 1 and block_start(blocks[-2]) + len(blocks[-2]) * min_gap > block_start(blocks[-1]):
            last = blocks.pop()
            blocks[-1].extend(last)

    positions = [0.0] * len(targets)
    floor = lower if lower is not None else float("-inf")
    for block in blocks:
        start = max(block_start(block), floor)
        for offset, k in enumerate(block):
            positions[order[k]] = start + offset * min_gap
        floor = start + len(block) * min_gap

    if upper is not None and positions:
        overflow = max(positions) - upper
        if overflow > 0:  # push everything down, then re-apply spacing from the top
            ceiling = upper
            for k in reversed(range(len(order))):
                i = order[k]
                positions[i] = min(positions[i], ceiling)
                ceiling = positions[i] - min_gap
    return positions
