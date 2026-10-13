import pytest

from climbing_graphs.grades import FONT_BOULDER, FRENCH_SPORT, V_BOULDER, font_with_v, normalize_grade


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("8B+", "8B+"),
        ("8b +", "8B+"),
        ("8B +", "8B+"),  # non-breaking space
        ("8B +", "8B+"),  # thin space
        ("8Bplus", "8B+"),
        ("", None),
        (None, None),
        (float("nan"), None),
    ],
)
def test_normalize_grade(raw, expected):
    assert normalize_grade(raw) == expected


def test_scales_are_ordered():
    assert FONT_BOULDER.position("8C+") == FONT_BOULDER.position("8C") + 1
    assert FRENCH_SPORT.position("9a") == FRENCH_SPORT.position("8c+") + 1
    assert V_BOULDER.position("V16") == 16


@pytest.mark.parametrize(
    "scale, split, low, high",
    [
        (FRENCH_SPORT, "9a/9a+", "9a", "9a+"),
        (FRENCH_SPORT, "8a/+", "8a", "8a+"),
        (V_BOULDER, "V10/11", "V10", "V11"),
        (V_BOULDER, "V15/16", "V15", "V16"),
    ],
)
def test_split_grades_sit_halfway(scale, split, low, high):
    assert scale.position(split) == (scale.position(low) + scale.position(high)) / 2


def test_unknown_grade():
    assert "10a" not in FRENCH_SPORT
    with pytest.raises(KeyError):
        FRENCH_SPORT.position("10a")


def test_labels_use_scale_case():
    assert FRENCH_SPORT.label("9B+") == "9b+"
    assert FONT_BOULDER.label("8c+") == "8C+"
    assert font_with_v("8c+") == "8C+ (V16)"


def test_ticks_fill_whole_grades_and_keep_used_splits():
    values, labels = V_BOULDER.ticks(["V8", "V10/11", "V12"])
    assert labels == ["V8", "V9", "V10", "V10/11", "V11", "V12"]
    assert values == sorted(values)
