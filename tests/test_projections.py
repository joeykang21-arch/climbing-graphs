import numpy as np
import pytest

from climbing_graphs.projections import MODELS, project


def test_evenly_spaced_data_gives_the_same_answer_from_every_model():
    projection = project(np.array([0, 1, 2, 3]), np.array([2000, 2004, 2008, 2012]), target=5)
    for model in MODELS:
        assert projection.at_target(model) == pytest.approx(2020)


def test_projection_starts_at_the_first_known_point():
    projection = project(np.array([13, 14, 15]), np.array([2002.7, 2011.9, 2025.5]), target=16)
    assert projection.positions.tolist() == [13, 14, 15, 16]
    assert projection.years["linear_gap"][0] == pytest.approx(2002.7)
    assert projection.years["exp_gap"][0] == pytest.approx(2002.7)


def test_gap_models_reproduce_two_gaps_exactly():
    # With two gaps, both gap models pass through every known point.
    projection = project(np.array([13, 14, 15]), np.array([2002.0, 2011.0, 2025.0]), target=16)
    for model in ("linear_gap", "exp_gap"):
        assert projection.years[model][:3] == pytest.approx([2002, 2011, 2025])
    assert projection.at_target("linear_gap") == pytest.approx(2025 + 19)
    assert projection.at_target("exp_gap") == pytest.approx(2025 + 14 * 14 / 9)


def test_missing_grade_is_spread_over_the_steps_it_spans():
    # Constant 3 years per grade, but grade 2 is missing from the data.
    full = project(np.array([0, 1, 2, 3, 4]), np.array([0, 3, 6, 9, 12.0]), target=6)
    gappy = project(np.array([0, 1, 3, 4]), np.array([0, 3, 9, 12.0]), target=6)
    for model in MODELS:
        assert gappy.at_target(model) == pytest.approx(full.at_target(model))


def test_negative_gaps_do_not_break_the_exponential_model():
    projection = project(np.array([0, 1, 2, 3]), np.array([1960, 1958, 1970, 1990.0]), target=5)
    assert np.isfinite(projection.years["exp_gap"]).all()


def test_needs_three_points():
    with pytest.raises(ValueError):
        project(np.array([0, 1]), np.array([2000, 2001]), target=3)
