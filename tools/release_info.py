"""Facts about a release, read from the repository. Used by .github/workflows/release.yaml and by tests/test_release.py.

    python tools/release_info.py version              print the package version
    python tools/release_info.py notes VERSION        print the CHANGELOG.md section of VERSION
    python tools/release_info.py check-tag TAG        check that TAG may be released
    python tools/release_info.py is-prerelease VERSION  print true or false

Only the standard library is used, so it runs before anything is installed.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
INIT = ROOT / "ha_blueprint_test_harness" / "__init__.py"
CHANGELOG = ROOT / "CHANGELOG.md"
# 1.2.3, optionally a pre-release (a1, b2, rc3) and optionally .devN.
VERSION = re.compile(r"^\d+\.\d+\.\d+((a|b|rc)\d+)?(\.dev\d+)?$")


# Reads __version__ from the package file as text, without importing the package (which needs Home Assistant).
def package_version(path: pathlib.Path = INIT) -> str:
    match = re.search(r'^__version__ = "([^"]+)"', path.read_text(encoding="utf-8"), re.M)
    if not match or not VERSION.match(match.group(1)):
        raise SystemExit(f"{path.name} has no valid __version__")
    return match.group(1)


# The versions that have a released section in the changelog, in the order they appear.
def released_versions(text: str) -> list[str]:
    return re.findall(r"^## \[(\d+\.\d+\.\d+[^\]]*)\] - \d{4}-\d{2}-\d{2}$", text, re.M)


# The rule violations in a changelog: it must start with an Unreleased section, released versions must go down from
# top to bottom, and each released section must have a 'Tested with:' line. An empty list means it is fine.
def changelog_problems(text: str) -> list[str]:
    problems = []
    headings = re.findall(r"^## .*$", text, re.M)
    if not headings or headings[0] != "## [Unreleased]":
        problems.append("the first section must be '## [Unreleased]'")
    versions = released_versions(text)
    key = lambda version: tuple(int(part) for part in re.match(r"(\d+)\.(\d+)\.(\d+)", version).groups())
    if versions != sorted(versions, key=key, reverse=True):
        problems.append("released versions must be listed newest first")
    for version in versions:
        if "Tested with:" not in notes(text, version):
            problems.append(f"version {version} has no 'Tested with:' line")
    return problems


# The text of one released section of the changelog, from its heading to the next version heading.
def notes(text: str, version: str) -> str:
    match = re.search(rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}\n(.*?)(?=^## \[|\Z)", text, re.S | re.M)
    if not match:
        raise SystemExit(f"CHANGELOG.md has no released section for version {version}")
    return match.group(1).strip() + "\n"


# True for alpha, beta and release-candidate versions (1.2.3a1, 1.2.3b1, 1.2.3rc1).
def is_prerelease(version: str) -> bool:
    return re.search(r"(a|b|rc)\d+", version) is not None


# The reasons why TAG may not be released; an empty list means it may. The tag must be "v" plus the package
# version, the version must not be a development version, and the changelog must have a section for it.
def check_tag(tag: str, version: str, changelog: str) -> list[str]:
    problems = []
    if tag != f"v{version}":
        problems.append(f"tag {tag} does not match the package version v{version}")
    if ".dev" in version:
        problems.append(f"version {version} is a development version")
    if version not in released_versions(changelog):
        problems.append(f"CHANGELOG.md has no released section for {version}")
    return problems


# The command line: see the module docstring.
def main(argv: list[str]) -> int:
    command, args = (argv[0], argv[1:]) if argv else ("", [])
    if command == "version" and not args:
        print(package_version())
    elif command == "notes" and len(args) == 1:
        print(notes(CHANGELOG.read_text(encoding="utf-8"), args[0]), end="")
    elif command == "is-prerelease" and len(args) == 1:
        print("true" if is_prerelease(args[0]) else "false")
    elif command == "check-tag" and len(args) == 1:
        problems = check_tag(args[0], package_version(), CHANGELOG.read_text(encoding="utf-8"))
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1 if problems else 0
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
