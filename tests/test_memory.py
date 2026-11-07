"""The memory index (MEMORY.md) and its entries (memory/*.md) must agree, and an entry must not name things that are gone."""

import pathlib
import re

import pytest
from _docs import front_matter

ROOT = pathlib.Path(__file__).parents[1]
INDEX = ROOT / "MEMORY.md"
ENTRIES = sorted((ROOT / "memory").glob("*.md"))
TYPES = {"decision", "fact", "pitfall", "observation", "research"}
MAX_LINES = 40  # an entry longer than this should be split


# All files the index links to, as paths relative to the project.
def indexed_files() -> list[str]:
    return re.findall(r"\]\((memory/[^)]+\.md)\)", INDEX.read_text(encoding="utf-8"))


def test_there_are_entries():
    # An empty folder would make every other check in this file pass for nothing.
    assert len(ENTRIES) >= 1


def test_every_entry_is_in_the_index_exactly_once():
    # A file that is not in the index will never be found by an agent that reads only the index.
    linked = indexed_files()
    assert sorted(linked) == sorted(f"memory/{path.name}" for path in ENTRIES)


@pytest.mark.parametrize("path", ENTRIES, ids=lambda path: path.name)
def test_entry_has_the_required_front_matter(path):
    # Name matches the file, one-line description, a known type, a list of files, and a check date.
    header = front_matter(path)
    assert header["name"] == path.stem
    assert isinstance(header["description"], str) and "\n" not in header["description"].strip()
    assert 0 < len(header["description"]) <= 220
    meta = header["metadata"]
    assert meta["type"] in TYPES
    assert isinstance(meta["applies_to"], list)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(meta["checked"]))


@pytest.mark.parametrize("path", ENTRIES, ids=lambda path: path.name)
def test_files_an_entry_applies_to_still_exist(path):
    # A memory that names something that is gone is wrong (see AGENTS.md, rule 15).
    for name in front_matter(path)["metadata"]["applies_to"]:
        assert (ROOT / name).exists(), f"{path.name} names {name}, which does not exist"


@pytest.mark.parametrize("path", ENTRIES, ids=lambda path: path.name)
def test_entry_stays_short(path):
    # Short entries are what lets an agent read only what it needs.
    assert len(path.read_text(encoding="utf-8").splitlines()) <= MAX_LINES


def test_index_hooks_tell_when_to_read():
    # Every index line must say when to open the entry; that is the point of the index.
    lines = [line for line in INDEX.read_text(encoding="utf-8").splitlines() if re.search(r"\]\(memory/[^)]+\.md\)", line)]
    assert lines and all("read" in re.split(r"\.md\)", line, maxsplit=1)[1].lower() for line in lines)
