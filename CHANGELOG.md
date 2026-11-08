# Changelog

All notable changes to this project are written here, newest first. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). How versions are chosen is in [`RELEASING.md`](RELEASING.md).

## [Unreleased]

### Changed

- The harness works with `pytest-homeassistant` (maintained in Home Assistant core, tested with 2026.11.0) as well as with `pytest-homeassistant-custom-component`; the import in `env.py` uses the first and falls back to the second. If neither is installed, importing the harness raises an `ImportError` that says what to install.
- **The harness no longer depends on `pytest-homeassistant-custom-component`.** The two packages must not be installed together, so a hard dependency on one would force the other out. Install a test package yourself ([Getting started](docs/getting-started.md#2-install)). Projects that installed the harness for its dependency must add the package to their requirements.
- `pytest.ini` examples now contain `asyncio_default_fixture_loop_scope = function` and `addopts = -p no:respx`. The second is required with `pytest-homeassistant`.
- CI runs the tests with both packages (`tests` and `tests-custom-component`); `requirements-dev.txt` now pins `pytest-homeassistant==2026.11.0`, the old pin moved to `requirements-dev-custom-component.txt`.

## [0.1.0] - 2026-11-07

First release. Pre-1.0: the API may still change.

Tested with: Home Assistant 2026.10.4, `pytest-homeassistant-custom-component` 0.13.375, Python 3.14 (macOS and Ubuntu).

### Added

- `BlueprintEnv` and the `blueprint_env` pytest fixture: load an automation blueprint with `use_blueprint`, set states, fire events, advance a frozen clock, mock services and read the recorded calls.
- `Call`, `sets_state` and `BlueprintLoadError`.
- The mutation tool `python -m ha_blueprint_test_harness.mutate`: structural and Jinja-template mutations, the outcomes killed, survived, invalid and error, and the options `--timeout`, `--workdir` and `--fail-under`.
- `pyproject.toml`, so that the package can be built and installed.
- Licensed under the Apache License 2.0.
- Documentation in `docs/`: getting started, configuring a project, writing tests, mutation testing and troubleshooting, with runnable examples in `docs/examples/`.
