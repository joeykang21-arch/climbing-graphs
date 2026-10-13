"""Downloading and parsing the source tables.

Pages are cached under ``.cache/`` so repeated runs are fast and work offline.
A cached page is reused for ``CACHE_MAX_AGE`` and refetched after that; if the
refetch fails, the stale copy is used with a warning.
"""

from __future__ import annotations

import logging
import re
import time
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .dates import parse_ascent_date
from .grades import normalize_grade

log = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
CACHE_MAX_AGE = 24 * 60 * 60  # seconds
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; climbing-graphs)"}
_TIMEOUT = 30

IFSC_WINS_URL = "https://en.wikipedia.org/wiki/Ranking_of_career_IFSC_victories_by_climber"
_IFSC_SECTIONS = {"men": "Results_for_Men", "women": "Results_for_Women"}


def fetch_html(url: str, *, refresh: bool = False, cache_dir: Path = CACHE_DIR) -> str:
    """Return the page at ``url``, using the on-disk cache when it is fresh."""
    cache_file = cache_dir / (re.sub(r"[^A-Za-z0-9]+", "_", url).strip("_") + ".html")
    is_fresh = cache_file.exists() and time.time() - cache_file.stat().st_mtime < CACHE_MAX_AGE
    if is_fresh and not refresh:
        return cache_file.read_text(encoding="utf-8")

    try:
        response = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        if cache_file.exists():
            log.warning("Could not fetch %s (%s); using cached copy", url, exc)
            return cache_file.read_text(encoding="utf-8")
        raise

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(response.text, encoding="utf-8")
    return response.text


def read_ascent_list(url: str, *, refresh: bool = False) -> pd.DataFrame:
    """Read a climbing-history.org list into a tidy frame.

    Columns: ``climber``, ``climb``, ``grade`` (normalized key), ``date_text``
    (as published) and ``date`` (parsed, may be NaT).
    """
    table = pd.read_html(StringIO(fetch_html(url, refresh=refresh)), flavor="bs4")[0]
    return tidy_ascent_table(table)


def tidy_ascent_table(table: pd.DataFrame) -> pd.DataFrame:
    """Normalize a raw climbing-history table (see ``read_ascent_list``)."""
    columns = {str(c).strip().lower(): c for c in table.columns}
    try:
        climber, climb, grade = columns["climber"], columns["climb"], columns["grade"]
    except KeyError as exc:
        raise ValueError(f"Unexpected table layout, columns were {list(table.columns)}") from exc
    date_col = next((c for name, c in columns.items() if "date" in name), None)

    df = pd.DataFrame(
        {
            "climber": table[climber].astype("string").str.strip(),
            "climb": table[climb].astype("string").str.strip(),
            "grade": table[grade].map(normalize_grade),
            "date_text": table[date_col] if date_col is not None else pd.NA,
        }
    )
    df["date"] = df["date_text"].map(parse_ascent_date)
    df = df.dropna(subset=["climber", "grade"])
    return df.reset_index(drop=True)


def read_ifsc_wins(gender: str, *, refresh: bool = False) -> pd.DataFrame:
    """Career IFSC wins for ``"men"`` or ``"women"``.

    The Wikipedia tables are located by their section heading rather than by
    position, because the page's table order has changed over time.

    Columns: ``climber``, ``lead``, ``boulder``, ``speed``, ``combined``.
    """
    html = fetch_html(IFSC_WINS_URL, refresh=refresh)
    heading = BeautifulSoup(html, "lxml").find(id=_IFSC_SECTIONS[gender])
    if heading is None:
        raise ValueError(f"Section {_IFSC_SECTIONS[gender]!r} not found on {IFSC_WINS_URL}")
    table = pd.read_html(StringIO(str(heading.find_next("table"))))[0]
    return tidy_ifsc_table(table)


def tidy_ifsc_table(table: pd.DataFrame) -> pd.DataFrame:
    """Flatten the multi-row Wikipedia header and keep the career-total columns."""
    if isinstance(table.columns, pd.MultiIndex):
        table.columns = [str(c[-1]).strip() for c in table.columns]
    first = table["First Name"].astype("string").str.strip().fillna("")
    last = table["Last Name"].astype("string").str.strip().fillna("")

    df = pd.DataFrame({"climber": (first + " " + last).str.strip()})
    # The first L/B/S/C columns are career totals (later ones are per-event splits).
    for short, name in [("L", "lead"), ("B", "boulder"), ("S", "speed"), ("C", "combined")]:
        df[name] = pd.to_numeric(table[short], errors="coerce")

    is_junk = df["climber"].str.lower().isin(["", "first name last name", "total total"])
    df = df[~is_junk].dropna(subset=["lead", "boulder", "speed", "combined"], how="all")
    return df.fillna(0).reset_index(drop=True)
