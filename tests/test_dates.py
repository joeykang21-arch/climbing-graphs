import pandas as pd
import pytest

from climbing_graphs.dates import decimal_year, parse_ascent_date


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("11th Nov 2025", "2025-11-11"),
        ("1st Jun 2015", "2015-06-01"),
        ("2019", "2019-01-01"),
        ("Mar 2021", "2021-03-01"),
        ("Sep 2002", "2002-09-01"),
        ("Before 25th Feb 2008", "2008-02-25"),
        ("9th-10th March 2025", "2025-03-09"),
        ("13th-23rd October 2025", "2025-10-13"),
        ("1st October-1st December 2025", "2025-10-01"),
        ("20th September 2023-1st January 2024", "2023-09-20"),
        ("between 3rd May 2020 and 7th June 2020", "2020-05-03"),
        ("2025-03-01", "2025-03-01"),
    ],
)
def test_parse_ascent_date(raw, expected):
    assert parse_ascent_date(raw) == pd.Timestamp(expected)


@pytest.mark.parametrize("raw", [None, float("nan"), "", "   ", "sometime"])
def test_unparseable_dates_are_nat(raw):
    assert pd.isna(parse_ascent_date(raw))


def test_decimal_year():
    assert decimal_year(pd.Timestamp("2020-01-01")) == 2020.0
    assert decimal_year(pd.Timestamp("2021-07-02 12:00")) == pytest.approx(2021.5)
