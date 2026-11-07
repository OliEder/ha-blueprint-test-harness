"""ROADMAP.md (a table of milestones), roadmap/M*.md (one file per milestone with content) and roadmap/log/ (a monthly log) must agree."""

import pathlib
import re

import pytest
from _docs import front_matter

ROOT = pathlib.Path(__file__).parents[1]
ROADMAP = ROOT / "ROADMAP.md"
ITEMS = sorted((ROOT / "roadmap").glob("M*.md"))
LOGS = sorted((ROOT / "roadmap" / "log").glob("*.md"))
STATES = {"open", "active", "done", "idea", "direction"}
ROW = re.compile(r"^\| (M\d+) \| (.+?) \| (\w+) \| (.+?) \|$", re.M)
ENTRY = re.compile(r"^- \*\*(\d{4}-\d{2}-\d{2})\*\* · ")
MAX_ROADMAP_LINES = 100
MAX_ITEM_LINES = 60


# The rows of the milestone table as (id, title, state, detail cell).
def rows() -> list[tuple[str, str, str, str]]:
    return ROW.findall(ROADMAP.read_text(encoding="utf-8"))


# The milestone file a detail cell links to, or None for a dash.
def linked_file(detail: str) -> str | None:
    match = re.search(r"\]\((roadmap/[^)]+\.md)\)", detail)
    return match.group(1) if match else None


def test_the_table_has_milestones_with_unique_ids():
    # An empty or duplicated table would make the other checks pass for nothing.
    ids = [row[0] for row in rows()]
    assert ids and len(ids) == len(set(ids))


@pytest.mark.parametrize("row", rows(), ids=lambda row: row[0])
def test_every_state_is_a_known_word(row):
    # The state of a milestone is one word from a fixed list, so that it can be read by a tool.
    assert row[2] in STATES, f"{row[0]}: unknown state {row[2]!r}"


@pytest.mark.parametrize("row", rows(), ids=lambda row: row[0])
def test_every_detail_link_points_to_a_file(row):
    # A link in the table to a file that does not exist is wrong.
    target = linked_file(row[3])
    assert row[3] == "—" or target, f"{row[0]}: the detail cell is neither a dash nor a link to roadmap/"
    if target:
        assert (ROOT / target).is_file(), f"{row[0]} links to {target}, which does not exist"


def test_every_milestone_file_is_in_the_table_exactly_once():
    # A file the table does not link will not be found by someone who reads only the table.
    linked = [linked_file(row[3]) for row in rows() if linked_file(row[3])]
    assert sorted(linked) == sorted(f"roadmap/{path.name}" for path in ITEMS)


def test_a_finished_milestone_has_no_file():
    # When a milestone is done its file is deleted; what is still true goes to memory/ or the README.
    assert [row[0] for row in rows() if row[2] == "done" and linked_file(row[3])] == []


@pytest.mark.parametrize("path", ITEMS, ids=lambda path: path.name)
def test_milestone_file_has_the_required_front_matter(path):
    # The id matches the file name and the table row that links it; the state is NOT repeated here.
    header = front_matter(path)
    assert path.name.startswith(header["id"] + "-")
    assert header["id"] in {row[0] for row in rows() if linked_file(row[3]) == f"roadmap/{path.name}"}
    assert isinstance(header["title"], str) and header["title"].strip()
    assert isinstance(header["description"], str) and "\n" not in header["description"].strip()
    assert 0 < len(header["description"]) <= 220
    meta = header["metadata"]
    assert meta["type"] == "roadmap-item"
    assert "state" not in meta and "state" not in header, "the state lives only in the table in ROADMAP.md"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(meta["updated"]))


@pytest.mark.parametrize("path", ITEMS, ids=lambda path: path.name)
def test_milestone_dependencies_and_files_exist(path):
    # depends_on names milestones that exist; applies_to names files that exist (a name for something gone is wrong).
    meta = front_matter(path)["metadata"]
    known = {row[0] for row in rows()}
    assert set(meta["depends_on"]) <= known, f"{path.name} depends on unknown {set(meta['depends_on']) - known}"
    for name in meta["applies_to"]:
        assert (ROOT / name).exists(), f"{path.name} names {name}, which does not exist"


@pytest.mark.parametrize("path", ITEMS, ids=lambda path: path.name)
def test_milestone_file_stays_short(path):
    # Short files are what lets an agent read only what it needs.
    assert len(path.read_text(encoding="utf-8").splitlines()) <= MAX_ITEM_LINES


def test_roadmap_stays_short():
    # ROADMAP.md is an index; when it grows, the content belongs in roadmap/.
    assert len(ROADMAP.read_text(encoding="utf-8").splitlines()) <= MAX_ROADMAP_LINES


def test_log_files_are_named_by_month():
    # One file per month, named YYYY-MM.md, so that a reader opens only the recent past.
    assert LOGS and all(re.fullmatch(r"\d{4}-\d{2}\.md", path.name) for path in LOGS)


@pytest.mark.parametrize("path", LOGS, ids=lambda path: path.name)
def test_log_entries_are_dated_within_their_month_and_newest_first(path):
    # Every entry line starts with a date inside the file's month; entries are not in increasing order.
    dates = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- "):
            match = ENTRY.match(line)
            assert match, f"{path.name}: an entry must start with '- **YYYY-MM-DD** · ': {line[:60]}"
            dates.append(match.group(1))
    assert dates, f"{path.name} has no entries"
    assert all(date.startswith(path.stem) for date in dates)
    assert dates == sorted(dates, reverse=True)


def test_roadmap_links_the_newest_log():
    # ROADMAP.md points to the current month's log.
    assert f"roadmap/log/{LOGS[-1].name}" in ROADMAP.read_text(encoding="utf-8")
