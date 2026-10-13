"""Hand-curated "first ascent of the grade" milestones.

Each list records when a grade was first achieved in a given style. Where only
the year is known the date is 1 January. Edit these lists to update the
frontier and gap charts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Milestone:
    when: date
    grade: str
    climb: str = ""


def _m(year: int, grade: str, climb: str = "", month: int = 1, day: int = 1) -> Milestone:
    return Milestone(date(year, month, day), grade, climb)


# --- Sport: hardest redpoint ---------------------------------------------------

SPORT_REDPOINT_MEN = [
    _m(1983, "8a+", "The Face"),
    _m(1984, "8b", "Kanal im Rücken"),
    _m(1985, "8b+", "Punks in the Gym"),
    _m(1987, "8c", "Wallstreet"),
    _m(1990, "8c+", "Hubble", month=6),
    _m(1991, "9a", "Action Directe"),
    _m(2001, "9a+", "Realization", month=7),
    _m(2008, "9b", "Jumbo Love", month=9, day=11),
    _m(2012, "9b+", "Change", month=10, day=4),
    _m(2017, "9c", "Silence", month=9, day=3),
]

SPORT_REDPOINT_WOMEN = [
    _m(1986, "8a"),
    _m(1988, "8a+"),
    _m(1988, "8b"),
    _m(1990, "8b+"),
    _m(1998, "8c"),
    _m(2000, "8c+"),
    _m(2002, "9a"),
    _m(2005, "9a/9a+"),
    _m(2017, "9a+"),
    _m(2017, "9b"),
    _m(2025, "9b+"),
]

# --- Sport: hardest flash or onsight (whichever came first) ----------------------

SPORT_FLASH_ONSIGHT_MEN = [
    _m(1982, "7b+", "Super Crack / Captain Crochet"),
    _m(1982, "7c", "Equinox / La Polka des Ringards"),
    _m(1984, "7c+", "Pol Pot"),
    _m(1987, "8a", "Samizdat"),
    # first men's 8a+ flash/onsight is unknown, so the grade is skipped
    _m(1993, "8b", "Liaisons Dangereuses"),
    _m(1995, "8b+", "Massey Fergusson"),
    _m(2004, "8c", "White Zombie", month=10, day=6),
    _m(2007, "8c+", "Bizi Euskaraz", month=12, day=11),
    _m(2012, "9a", "Southern Smoke Direct (flash)", month=10, day=29),
    _m(2018, "9a+", "Super Crackinette (flash)", month=2, day=10),
]

SPORT_FLASH_ONSIGHT_WOMEN = [
    _m(1992, "8a"),
    _m(1993, "8a/+"),
    _m(2000, "8a+"),
    _m(2004, "8b"),
    _m(2006, "8b+"),
    _m(2015, "8c", "La Fabelita (flash)"),
    _m(2025, "8c+"),
]

# --- Bouldering: hardest ascent ------------------------------------------------------

BOULDER_MEN = [
    _m(1946, "V3"),
    _m(1953, "V6"),
    _m(1958, "V8"),
    _m(1959, "V9"),
    _m(1975, "V12"),
    _m(1978, "V10"),  # does not advance the frontier
    _m(1984, "V11"),  # does not advance the frontier
    _m(1992, "V13", "La Danse des Balrogs"),
    _m(1996, "V14", "Radja"),
    _m(2002, "V15", "Monkey Wedding", month=8),
    _m(2008, "V16", "Gioia", month=2),  # "before 25 Feb 2008" per climbing-history.org
    _m(2016, "V17", "Burden of Dreams", month=10, day=24),
    _m(2025, "V18", "Exodia", month=11, day=11),
]

BOULDER_WOMEN = [
    _m(1989, "V8"),
    _m(1996, "V9"),
    _m(1997, "V10"),
    _m(1998, "V10/11"),
    _m(1998, "V11"),
    _m(1999, "V12"),
    _m(2002, "V14"),
    _m(2003, "V15"),
    _m(2023, "V15/16"),
    _m(2025, "V16"),
]

# --- Bouldering: hardest flash --------------------------------------------------------

BOULDER_FLASH_MEN = [
    _m(2002, "V13", "Shadowfax", month=9),
    _m(2011, "V14", "Entlinge", month=11, day=28),
    _m(2025, "V15", "Foundation's Edge", month=7, day=9),
]
