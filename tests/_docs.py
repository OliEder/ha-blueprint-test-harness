"""Small helpers shared by the tests that check the project's own documents."""

import pathlib

import yaml


# Reads the header block between the two '---' lines of a document and returns it as a dictionary.
def front_matter(path: pathlib.Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path.name}: no front matter"
    header = text.split("\n---\n", 1)[0].removeprefix("---\n")
    return yaml.safe_load(header)
