import pandas as pd
import pytest

from climbing_graphs.grades import FONT_BOULDER, FRENCH_SPORT
from climbing_graphs.scoring import SCHEMES, describe_weights, score_climbers


def ascents(rows):
    return pd.DataFrame(rows, columns=["climber", "grade"])


FLASHES = ascents(
    [("A", "8C"), ("A", "8B"), ("B", "8B+"), ("B", "8B+"), ("C", "8B"), ("C", "8B"), ("C", "8B"), ("D", "8B")]
)


def test_exponential_scheme_is_18_5_1_from_the_top():
    ranking = score_climbers(FLASHES, SCHEMES["exponential"], FONT_BOULDER)
    assert ranking.weights == {"8C": 18, "8B+": 5, "8B": 1}
    assert list(ranking.weights) == ["8C", "8B+", "8B"]  # hardest first
    assert dict(zip(ranking.table["climber"], ranking.table["score"])) == {"A": 19, "B": 10, "C": 3, "D": 1}


def test_conservative_scheme_is_4_2_1():
    ranking = score_climbers(FLASHES, SCHEMES["conservative"], FONT_BOULDER)
    assert ranking.weights == {"8C": 4, "8B+": 2, "8B": 1}


def test_rarity_scheme_uses_ascent_counts():
    # 5 x 8B, 2 x 8B+, 1 x 8C  ->  8B = 1, 8B+ = 5/2, 8C = 5/1
    ranking = score_climbers(FLASHES, SCHEMES["rarity"], FONT_BOULDER)
    assert ranking.weights == {"8C": 5.0, "8B+": 2.5, "8B": 1.0}
    assert ranking.table.set_index("climber").loc["A", "score"] == 6


def test_equal_scheme_counts_ascents():
    ranking = score_climbers(FLASHES, SCHEMES["equal"], FONT_BOULDER)
    assert ranking.table.iloc[0].tolist()[:2] == ["C", 3]


def test_top_grade_weights_with_only_two_grades():
    # Grades arrive normalized (uppercase) from sources.tidy_ascent_table.
    onsights = ascents([("A", "9A"), ("B", "8C+")])
    ranking = score_climbers(onsights, SCHEMES["exponential"], FRENCH_SPORT)
    assert ranking.weights == {"9A": 18, "8C+": 5}


def test_grades_beyond_the_third_score_nothing_and_climbers_with_zero_are_dropped():
    data = ascents([("A", "9A+"), ("B", "9A"), ("C", "8C+"), ("D", "8C")])
    ranking = score_climbers(data, SCHEMES["exponential"], FONT_BOULDER)
    assert ranking.weights["8C"] == 0
    assert "D" not in set(ranking.table["climber"])


def test_grades_off_the_scale_are_ignored():
    data = ascents([("A", "8B"), ("B", "nonsense")])
    ranking = score_climbers(data, SCHEMES["equal"], FONT_BOULDER)
    assert ranking.table["climber"].tolist() == ["A"]


def test_ties_are_broken_alphabetically():
    data = ascents([("Zed", "8B"), ("Amy", "8B")])
    ranking = score_climbers(data, SCHEMES["equal"], FONT_BOULDER)
    assert ranking.table["climber"].tolist() == ["Amy", "Zed"]


def test_detail_lists_counts_per_grade():
    ranking = score_climbers(FLASHES, SCHEMES["exponential"], FONT_BOULDER)
    detail = ranking.table.set_index("climber").loc["A", "detail"]
    assert detail == "8C: 1<br>8B: 1"


def test_describe_weights():
    assert describe_weights({"9C": 18.0, "9B+": 5.0, "9B": 1.0}, FRENCH_SPORT) == "9c = 18 · 9b+ = 5 · 9b = 1"
    assert describe_weights({"8C": 37.0, "8B+": 6.475}, FONT_BOULDER) == "8C = 37 · 8B+ = 6.47"


@pytest.mark.parametrize("scheme", list(SCHEMES))
def test_every_scheme_ranks_without_error(scheme):
    ranking = score_climbers(FLASHES, SCHEMES[scheme], FONT_BOULDER)
    assert ranking.table["score"].is_monotonic_decreasing
