# Versions and releases

How version numbers are chosen, what counts as a breaking change, and how a release is made. The version is the one in `ha_blueprint_test_harness/__init__.py`; what changed per version is in [`CHANGELOG.md`](CHANGELOG.md).

## Version numbers

`MAJOR.MINOR.PATCH`, for example `0.2.1`, following [Semantic Versioning](https://semver.org/) in the form that Python packaging accepts ([PEP 440](https://peps.python.org/pep-0440/)). Pre-releases are written `0.2.0rc1`, development versions `0.2.0.dev0`. A release tag is the version with a `v` in front: `v0.2.0`.

**Before 1.0** the API may still change: a breaking change raises the MINOR number, never the PATCH number. **1.0.0** comes when the public API has been stable for a release cycle, the supported Home Assistant generations are defined and tested on every release (milestone M4), and every use of a Home Assistant internal sits behind one module (milestone M3).

## What the version covers: the public API

A change to any of these is visible to users and is versioned. Everything else (names starting with an underscore, the tests, the documents) is not.

- **Python names** exported by the package (`__all__`): `BlueprintEnv` (with `start`, `set_state`, `fire_event`, `advance`, `settle`, `render`, `last_trace`, `calls`, `calls_to`), `Call` (with `name`, `data`, `entity_ids`), `Trace` (with `path`, `variables`, `steps`, `run_id`, `error`), `MockConfigEntry` (re-exported from the installed test package), `sets_state` and `BlueprintLoadError`.
- **The pytest plugin and fixture:** the module `ha_blueprint_test_harness.pytest_plugin`, which users name in `pytest_plugins`, and the fixture `blueprint_env` it provides.
- **The mutation command** `python -m ha_blueprint_test_harness.mutate`: its options (`--timeout`, `--workdir`, `--fail-under`, the `--` before the test command), its exit codes (0 fine; 1 the score is below `--fail-under`, or the tests fail on the unchanged blueprint; 2 a test run itself broke) and its outcome names `killed`, `survived`, `invalid` and `error`.
- **The environment variables** `HA_BLUEPRINT_TEST_HARNESS_ORIGINAL` and `HA_BLUEPRINT_TEST_HARNESS_MUTANT`, through which the mutation command and the harness talk to each other.
- **The supported Python and Home Assistant versions.**

## Which number to raise

| Change | Before 1.0 | From 1.0 |
| --- | --- | --- |
| Remove or rename something public, or change what it means | MINOR | MAJOR |
| Drop support for a Python or Home Assistant generation | MINOR | MAJOR |
| Add something public, or support a new generation | MINOR | MINOR |
| Add a mutation operator (it can lower the score of an existing run: say so in the changelog) | MINOR | MINOR |
| Fix a bug, change documents, refactor inside | PATCH | PATCH |

When in doubt, raise the larger number.

## Home Assistant and Python versions

The harness version is independent of Home Assistant's. Home Assistant releases every month, with patch releases in between, so every release states in the changelog what it was tested with, on a line that starts with `Tested with:` (Home Assistant version, test-package version, Python version). Until the version matrix exists (milestone M4), one generation is tested; other versions may work and are unverified.

The package depends on neither `pytest-homeassistant` nor `pytest-homeassistant-custom-component` (they must not be installed together, and it must not clash with a pin in a project that uses one). Both are tested in CI: `requirements-dev.txt` (the first) and `requirements-dev-custom-component.txt` (the second). The `Tested with:` line names both.

## Where the version lives

One place: `__version__` in `ha_blueprint_test_harness/__init__.py`. `pyproject.toml` reads it from there, the changelog heading and the release tag must equal it, and `tools/release_info.py` checks the last two. Do not write the number anywhere else.

## The changelog

Every change that a user can see (the public API above, behaviour, supported versions) gets one line under `## [Unreleased]` in the same pull request, in the group `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed` or `Security`. A released version has a heading `## [X.Y.Z] - YYYY-MM-DD` and a `Tested with:` line.

## Making a release

A maintainer makes a release. An agent may prepare the release commit and draft the notes; it does not create or push a tag and does not publish.

**Before you start**

- A `LICENSE` file exists.
- `main` is green: the `tests` and `mutation` jobs of `.github/workflows/ci.yaml`.
- The documents are current: walk the table "Keeping the documents current" in `AGENTS.md`, and update `status/numbers.md`.
- `status/open.md` has nothing that blocks the release.

**Steps**

1. Choose the version from the table above.
2. Set `__version__` in `ha_blueprint_test_harness/__init__.py` to `X.Y.Z`.
3. In `CHANGELOG.md` rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD`, add the `Tested with:` line (the numbers are in `status/numbers.md`), and put a new, empty `## [Unreleased]` above it.
4. Check locally: run the tests, `python tools/release_info.py notes X.Y.Z` (shows the release notes), and `uv build` (builds the package).
5. Commit as `Release X.Y.Z` and merge it into `main`. Then run the release workflow by hand on `main` (Actions, Release, Run workflow): a dry run that does everything except create the release and needs no tag. A tag cannot be moved or deleted, so fix what the dry run shows before you tag.
6. Tag that commit `vX.Y.Z` and push the tag with `git push origin vX.Y.Z`. Do not create a release in the GitHub web interface: the workflow creates the draft, and a release made by hand next to it gives two releases for one tag (this happened with 0.1.0; see `memory/first-release-lessons.md`).
7. `.github/workflows/release.yaml` runs: it checks that the tag equals the version and that the changelog has the section, runs the tests, builds the source archive and the wheel, and creates a **draft** GitHub release with both files and the changelog section as notes. Review the draft and publish it.
8. Update the line about supported versions in `SECURITY.md`. Add a line to `roadmap/log/`, and update `status/numbers.md` and, if a milestone is done, its row in `ROADMAP.md`.

**After the release**

Set `__version__` on `main` to the next development version, for example `0.2.0.dev0`. The release check refuses a tag on a development version, so a tag on `main` by mistake fails instead of publishing.

## When a release is wrong

Do not move or delete a published tag. Fix the problem on a branch from the tag, publish the next PATCH version, and add a warning to the notes of the broken release. If the release is on a package index, yank it there.

## Where releases are published

On GitHub, as a release with the source archive and the wheel attached. Install from the wheel: `pip install ha_blueprint_test_harness-X.Y.Z-py3-none-any.whl`. Publishing to PyPI is not done yet; it would use PyPI's trusted publishing from the release workflow, with no token stored in the repository (milestone M9).
