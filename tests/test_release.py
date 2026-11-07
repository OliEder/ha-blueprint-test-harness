"""Version, changelog, release tool and public API must agree with each other."""

import importlib.util
import pathlib
import re
import tomllib

import pytest

ROOT = pathlib.Path(__file__).parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"
RELEASING = ROOT / "RELEASING.md"


# Loads tools/release_info.py as a module (it is a script, not part of the package).
def load_tool():
    spec = importlib.util.spec_from_file_location("release_info", ROOT / "tools" / "release_info.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOL = load_tool()
SAMPLE = """# Changelog

## [Unreleased]

### Added

- something new

## [0.2.0] - 2026-12-01

### Fixed

- a fix

Tested with: Home Assistant 2026.12.0, Python 3.14.

## [0.1.0] - 2026-11-20

### Added

- first

Tested with: Home Assistant 2026.10.4, Python 3.14.
"""


def test_the_package_version_is_a_valid_version():
    # The version is read from the file as text and has the form 1.2.3, 1.2.3rc1 or 1.2.3.dev0.
    assert TOOL.VERSION.match(TOOL.package_version())


def test_the_imported_version_equals_the_one_in_the_file():
    # Importing the package gives the same version as reading the file, so there is one source.
    import ha_blueprint_test_harness

    assert ha_blueprint_test_harness.__version__ == TOOL.package_version()


def test_pyproject_takes_its_version_from_the_package():
    # The version is not written a second time in pyproject.toml.
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "version" in config["project"]["dynamic"] and "version" not in config["project"]
    assert config["tool"]["setuptools"]["dynamic"]["version"] == {"attr": "ha_blueprint_test_harness.__version__"}


def test_the_real_changelog_follows_the_rules():
    # Starts with Unreleased, newest version first, every released section says what it was tested with.
    assert TOOL.changelog_problems(CHANGELOG.read_text(encoding="utf-8")) == []


def test_a_good_sample_changelog_has_no_problems():
    # The sample used by the other tests is itself valid.
    assert TOOL.changelog_problems(SAMPLE) == []


@pytest.mark.parametrize("broken,expected", [
    (SAMPLE.replace("## [Unreleased]", "## [Next]"), "Unreleased"),
    (SAMPLE.replace("## [0.2.0] - 2026-12-01", "## [0.0.9] - 2026-12-01"), "newest first"),
    (SAMPLE.replace("Tested with: Home Assistant 2026.12.0, Python 3.14.\n", ""), "0.2.0 has no 'Tested with:'"),
    ("# Changelog\n", "Unreleased"),
])
def test_a_broken_changelog_is_reported(broken, expected):
    # Each rule has a case that breaks it; the message names the rule.
    assert any(expected in problem for problem in TOOL.changelog_problems(broken))


def test_a_released_package_version_has_a_changelog_section():
    # If the package is not a development version, the changelog must have its section.
    version = TOOL.package_version()
    if ".dev" not in version:
        assert version in TOOL.released_versions(CHANGELOG.read_text(encoding="utf-8"))


def test_notes_returns_exactly_the_requested_section():
    # The release notes of 0.2.0 contain its lines and none of its neighbours'.
    notes = TOOL.notes(SAMPLE, "0.2.0")
    assert "a fix" in notes and "first" not in notes and "something new" not in notes


def test_notes_for_a_missing_version_fail():
    # A version without a section is an error, not an empty release note.
    with pytest.raises(SystemExit):
        TOOL.notes(SAMPLE, "0.3.0")


@pytest.mark.parametrize("tag,version,ok", [
    ("v0.2.0", "0.2.0", True),
    ("v0.2.1", "0.2.0", False),           # the tag does not match the version
    ("0.2.0", "0.2.0", False),            # the tag has no 'v'
    ("v0.3.0.dev0", "0.3.0.dev0", False),  # a development version, and no changelog section
    ("v0.3.0", "0.3.0", False),           # no changelog section
])
def test_check_tag(tag, version, ok):
    # A tag may be released only if it is 'v' + the version, not a dev version, and has a changelog section.
    assert (TOOL.check_tag(tag, version, SAMPLE) == []) is ok


@pytest.mark.parametrize("version,expected", [("0.2.0", False), ("0.2.0rc1", True), ("0.2.0a2", True), ("0.2.0b1", True), ("0.2.0.dev0", False)])
def test_prerelease_detection(version, expected):
    # Alpha, beta and release candidates are marked as pre-releases on GitHub; final and dev versions are not.
    assert TOOL.is_prerelease(version) is expected


def test_every_exported_name_is_documented_as_public_api():
    # What the package exports is what RELEASING.md calls public; a new export must be listed there.
    import ha_blueprint_test_harness

    text = RELEASING.read_text(encoding="utf-8")
    missing = [name for name in ha_blueprint_test_harness.__all__ if f"`{name}`" not in text]
    assert not missing, f"not listed as public API in RELEASING.md: {missing}"


def test_the_mutation_interface_is_documented_as_public_api():
    # Outcome names, options and environment variables are part of the public API and are listed.
    text = RELEASING.read_text(encoding="utf-8")
    for item in ("killed", "survived", "invalid", "error", "--timeout", "--workdir", "--fail-under",
                 "HA_BLUEPRINT_TEST_HARNESS_ORIGINAL", "HA_BLUEPRINT_TEST_HARNESS_MUTANT", "blueprint_env"):
        assert f"`{item}`" in text, f"{item} is not listed in RELEASING.md"


def test_the_licence_is_apache_2_0_everywhere_it_is_stated():
    # The LICENSE file is the Apache 2.0 text, and the package metadata names the same licence.
    assert "Apache License\n                           Version 2.0, January 2004" in (ROOT / "LICENSE").read_text(encoding="utf-8")
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert config["project"]["license"] == "Apache-2.0" and config["project"]["license-files"] == ["LICENSE"]
