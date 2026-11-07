"""STATUS.md (an index and a map) and status/*.md (numbers, open items, commands) must agree, and the map must not name files that are gone."""

import pathlib
import re

import pytest
from _docs import front_matter

ROOT = pathlib.Path(__file__).parents[1]
STATUS = ROOT / "STATUS.md"
FILES = sorted((ROOT / "status").glob("*.md"))
MAX_INDEX_LINES = 60  # STATUS.md is an index; past this it should hand more to status/
MAX_FILE_LINES = 60
PATH_LIKE = re.compile(r"^[\w./-]+(\.(md|py|yaml|yml|ini|txt|toml)|/)$")


# The text of the "Project map by task" section of STATUS.md, up to the next heading.
def map_section() -> str:
    match = re.search(r"## Project map by task\n(.*?)(?=\n## |\Z)", STATUS.read_text(encoding="utf-8"), re.S)
    assert match, "STATUS.md has no 'Project map by task' section"
    return match.group(1)


# Finds a file or folder named in the map: a path with a folder is taken from the project root,
# a bare file name is looked up anywhere in the project (outside .venv and .git).
def resolve(token: str) -> bool:
    if "/" in token.rstrip("/"):
        return (ROOT / token).exists()
    if token.endswith("/"):
        return (ROOT / token).is_dir()
    return any(not {".venv", ".git", "__pycache__"} & set(p.parts) for p in ROOT.rglob(token))


def test_there_are_status_files():
    # An empty folder would make every other check in this file pass for nothing.
    assert len(FILES) >= 1


def test_every_status_file_is_in_the_index_exactly_once():
    # A file that is not linked from STATUS.md will not be found by someone who reads only the index.
    linked = re.findall(r"\]\((status/[^)]+\.md)\)", STATUS.read_text(encoding="utf-8"))
    assert sorted(linked) == sorted(f"status/{path.name}" for path in FILES)


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.name)
def test_status_file_has_the_required_front_matter(path):
    # Name matches the file, one-line description, type "status", an update date and a list of files.
    header = front_matter(path)
    assert header["name"] == path.stem
    assert isinstance(header["description"], str) and "\n" not in header["description"].strip()
    assert 0 < len(header["description"]) <= 220
    meta = header["metadata"]
    assert meta["type"] == "status"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(meta["updated"]))
    assert isinstance(meta["applies_to"], list)


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.name)
def test_files_a_status_file_applies_to_still_exist(path):
    # A status file that names something that is gone is wrong (see AGENTS.md, "Keeping the documents current").
    for name in front_matter(path)["metadata"]["applies_to"]:
        assert (ROOT / name).exists(), f"{path.name} names {name}, which does not exist"


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.name)
def test_status_file_stays_short(path):
    # Short files are what lets an agent read only what it needs.
    assert len(path.read_text(encoding="utf-8").splitlines()) <= MAX_FILE_LINES


def test_status_index_stays_short():
    # STATUS.md is an index; when it grows, the content belongs in status/.
    assert len(STATUS.read_text(encoding="utf-8").splitlines()) <= MAX_INDEX_LINES


def test_every_path_in_the_project_map_exists():
    # A map that points to a file that no longer exists is wrong; fix it the moment you notice.
    tokens = re.findall(r"`([^`]+)`", map_section())
    paths = [token for token in tokens if PATH_LIKE.match(token)]
    assert paths, "the map names no files"
    missing = [token for token in paths if not resolve(token)]
    assert not missing, f"the project map names files that do not exist: {missing}"


def test_index_hooks_tell_when_to_read():
    # Every status link must say when to open the file; that is the point of the index.
    lines = [line for line in STATUS.read_text(encoding="utf-8").splitlines() if re.search(r"\]\(status/[^)]+\.md\)", line)]
    assert lines and all("read" in re.split(r"\.md\)", line, maxsplit=1)[1].lower() for line in lines)
