import itertools

import pytest

from climbing_graphs.labels import spread_labels


def assert_spaced(positions, gap):
    for a, b in itertools.combinations(positions, 2):
        assert abs(a - b) >= gap - 1e-9


def test_separated_labels_stay_on_their_points():
    assert spread_labels([0, 10, 20], 1) == [0, 10, 20]


def test_overlapping_labels_spread_around_their_centre():
    positions = spread_labels([5, 5, 5], 1)
    assert sorted(positions) == pytest.approx([4, 5, 6])


def test_order_is_preserved_and_input_order_returned():
    targets = [3.0, 1.0, 1.2, 2.9, 1.1]
    positions = spread_labels(targets, 0.5)
    assert_spaced(positions, 0.5)
    by_target = [p for _, p in sorted(zip(targets, positions))]
    assert by_target == sorted(by_target)


def test_bounds_are_respected():
    positions = spread_labels([0, 0, 0, 10, 10, 10], 1, lower=0, upper=10)
    assert min(positions) >= 0
    assert max(positions) <= 10
    assert_spaced(positions, 1)


def test_empty():
    assert spread_labels([], 1, 0, 1) == []
