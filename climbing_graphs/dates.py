"""Parsing the free-form ascent dates used on climbing-history.org."""

from __future__ import annotations

import re
from datetime import date, datetime

import pandas as pd
from dateutil import parser as dateparser

_ORDINAL = re.compile(r"(\d+)(st|nd|rd|th)\b", re.IGNORECASE)
_BETWEEN = re.compile(r"^between\s+(.+?)\s+and\s+(.+)$", re.IGNORECASE)
_RANGE = re.compile(r"^(.+?)\s*[-–]\s*(.+)$")  # "1st-8th Sep 2022", "1st Oct-1st Dec 2025"
_BEFORE = re.compile(r"^before\s+(.+)$", re.IGNORECASE)
_YEAR_ONLY = re.compile(r"^\d{4}$")
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MONTH_YEAR = re.compile(r"^[A-Za-z]{3,9}\.?\s+\d{4}$")
_HAS_YEAR = re.compile(r"\d{4}")


def parse_ascent_date(raw: object) -> pd.Timestamp:
    """Best-effort parse of an ascent date. Returns ``NaT`` if it can't be parsed.

    Imprecise dates resolve to the earliest date they could mean:

    * ``"2019"`` -> 2019-01-01, ``"Mar 2021"`` -> 2021-03-01
    * ranges (``"9th-10th March 2025"``, ``"between X and Y"``) -> the start
    * ``"Before 25th Feb 2008"`` -> 2008-02-25 (the only date given)
    """
    if raw is None or (not isinstance(raw, str) and pd.isna(raw)):
        return pd.NaT
    text = _ORDINAL.sub(r"\1", str(raw).strip())
    if not text:
        return pd.NaT
    try:
        return pd.Timestamp(_parse(text))
    except (ValueError, OverflowError):
        return pd.NaT


def _parse(text: str) -> datetime:
    if _YEAR_ONLY.match(text):
        return datetime(int(text), 1, 1)
    if _ISO.match(text):
        return datetime.fromisoformat(text)
    if _MONTH_YEAR.match(text):
        return dateparser.parse(text, default=datetime(2000, 1, 1))

    match = _BEFORE.match(text)
    if match:
        return _parse(match.group(1))

    match = _BETWEEN.match(text) or _RANGE.match(text)
    if match and _HAS_YEAR.search(match.group(2)):
        end = _parse(match.group(2))
        # The start often omits month/year ("9-10 March 2025"); inherit them from the end.
        return dateparser.parse(match.group(1), default=end, dayfirst=True)

    return dateparser.parse(text, dayfirst=True)


def decimal_year(when: date | datetime | pd.Timestamp) -> float:
    """2012-10-04 -> 2012.76"""
    when = pd.Timestamp(when)
    start = pd.Timestamp(year=when.year, month=1, day=1)
    end = pd.Timestamp(year=when.year + 1, month=1, day=1)
    return when.year + (when - start) / (end - start)
