from datetime import date

from climbing_graphs.frontier import frontier_advances, frontier_by_year, frontier_gap
from climbing_graphs.grades import V_BOULDER
from climbing_graphs.milestones import Milestone


def m(year, grade):
    return Milestone(date(year, 1, 1), grade)


LEADER = [m(2000, "V10"), m(2003, "V12"), m(2001, "V9"), m(2003, "V11")]
FOLLOWER = [m(2001, "V8"), m(2004, "V10/11")]


def test_advances_keep_only_new_highs_one_per_year():
    advances = frontier_advances(LEADER, V_BOULDER)
    assert advances["year"].tolist() == [2000, 2003]
    assert advances["grade"].tolist() == ["V10", "V12"]


def test_frontier_by_year_carries_forward():
    frontier = frontier_by_year(LEADER, V_BOULDER, range(1999, 2005))
    assert frontier.isna().iloc[0]
    assert frontier.loc[2000:].tolist() == [10, 10, 10, 12, 12]


def test_gap_only_where_both_exist():
    gap = frontier_gap(LEADER, FOLLOWER, V_BOULDER, range(1999, 2006))
    assert gap.index.tolist() == [2001, 2002, 2003, 2004, 2005]
    assert gap.tolist() == [2, 2, 4, 1.5, 1.5]
