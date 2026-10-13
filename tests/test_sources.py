import pandas as pd

from climbing_graphs import sources

ASCENT_TABLE = pd.DataFrame(
    {
        "#": [1, 2, 3],
        "Climber": ["Adam Ondra ", "Will Bosi", None],
        "Climb": ["Silence", "Burden of Dreams", "Mystery"],
        "Grade": ["9c", "9A", "8B"],
        "Ascent Date": ["3rd Sep 2017", "Before 12th Apr 2023", "2019"],
    }
)


def test_tidy_ascent_table():
    df = sources.tidy_ascent_table(ASCENT_TABLE)
    assert df.columns.tolist() == ["climber", "climb", "grade", "date_text", "date"]
    assert df["climber"].tolist() == ["Adam Ondra", "Will Bosi"]  # stripped, missing climber dropped
    assert df["grade"].tolist() == ["9C", "9A"]
    assert df["date"].tolist() == [pd.Timestamp("2017-09-03"), pd.Timestamp("2023-04-12")]


def test_tidy_ascent_table_handles_date_column_first():
    table = ASCENT_TABLE.rename(columns={"Ascent Date": "Date"})[["Date", "Climber", "Climb", "Grade"]]
    assert sources.tidy_ascent_table(table)["date"].notna().all()


IFSC_HTML = """
<h2 id="Results_for_Women">Women</h2>
<table><tr><th>First Name</th><th>Last Name</th><th>L</th><th>B</th><th>S</th><th>C</th><th>T</th></tr>
<tr><td>Janja</td><td>Garnbret</td><td>8</td><td>5</td><td>0</td><td>7</td><td>20</td></tr></table>
<h2 id="Results_for_Men">Men</h2>
<table><tr><th>First Name</th><th>Last Name</th><th>L</th><th>B</th><th>S</th><th>C</th><th>T</th></tr>
<tr><td>Jakob</td><td>Schubert</td><td>7</td><td>0</td><td>0</td><td>6</td><td>13</td></tr>
<tr><td>First Name</td><td>Last Name</td><td>L</td><td>B</td><td>S</td><td>C</td><td>T</td></tr>
<tr><td>Speedy</td><td>McSpeed</td><td></td><td></td><td>9</td><td></td><td>9</td></tr></table>
"""


def test_ifsc_tables_are_found_by_heading_not_position(monkeypatch):
    monkeypatch.setattr(sources, "fetch_html", lambda url, refresh=False: IFSC_HTML)
    men = sources.read_ifsc_wins("men")
    women = sources.read_ifsc_wins("women")
    assert women["climber"].tolist() == ["Janja Garnbret"]
    assert men["climber"].tolist() == ["Jakob Schubert", "Speedy McSpeed"]  # repeated header row removed
    assert men.set_index("climber").loc["Speedy McSpeed"].tolist() == [0, 0, 9, 0]


def test_fetch_html_uses_fresh_cache(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("should not hit the network")

    monkeypatch.setattr(sources.requests, "get", fail)
    url = "https://example.com/list"
    (tmp_path / "https_example_com_list.html").write_text("<p>cached</p>", encoding="utf-8")
    assert sources.fetch_html(url, cache_dir=tmp_path) == "<p>cached</p>"


def test_fetch_html_falls_back_to_stale_cache_when_offline(tmp_path, monkeypatch):
    def offline(*args, **kwargs):
        raise sources.requests.ConnectionError("offline")

    monkeypatch.setattr(sources.requests, "get", offline)
    url = "https://example.com/list"
    (tmp_path / "https_example_com_list.html").write_text("<p>old</p>", encoding="utf-8")
    assert sources.fetch_html(url, refresh=True, cache_dir=tmp_path) == "<p>old</p>"
