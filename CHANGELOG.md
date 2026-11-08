# Changelog

All notable changes to this project are written here, newest first. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). How versions are chosen is in [`RELEASING.md`](RELEASING.md).

## [Unreleased]

## [0.4.0] - 2026-11-08

Pre-1.0: new public names are the reason for a MINOR version.

Tested with: Home Assistant 2026.11.0, `pytest-homeassistant` 2026.11.0, Python 3.14.3 (macOS) and Ubuntu (CI); also Home Assistant 2026.10.4 with `pytest-homeassistant-custom-component` 0.13.375, Python 3.14.3.

### Added

- `BlueprintEnv.start_automation(automation, pick=None, ...)`: runs an automation written directly (a dict, or a YAML file with one automation or a list as in `automations.yaml`), without a blueprint header.
- `responses=` for `start()` and `start_automation()`: services that return an answer (`weather.get_forecasts`) work with `response_variable`. The value is a dict or a function of the call.
- The mutation tool accepts an automation file, with `--pick` for a list. `start_automation(path)` swaps in the broken copy.
- `--jobs N` for the mutation tool: runs several mutants at the same time. Same result, in the same order; about 2 times faster with 4 jobs (measured).
- Documentation: "Test an automation you wrote directly" and two runnable examples (`car_driver`, `frost_warning`). It also says what does not work: device triggers (`device_id`) do not load, and `homeassistant: start` waits once for the event `homeassistant_started` in current Home Assistant versions (fire it with `fire_event`).

### Changed

- The message when a blueprint or automation does not come up now reads "the automation did not come up as a working automation".

### Fixed

- `start()` and `start_automation()` no longer fail with `BlueprintLoadError` when a test sets the state of another automation (a scenario in which the automation under test reads it, for example `last_triggered`). Only the automation created by the setup is checked.

## [0.3.0] - 2026-11-08

Pre-1.0: new public names are the reason for a MINOR version.

Tested with: Home Assistant 2026.11.0, `pytest-homeassistant` 2026.11.0, Python 3.14.3 (macOS) and Ubuntu (CI); also Home Assistant 2026.10.4 with `pytest-homeassistant-custom-component` 0.13.375, Python 3.14.3.

### Added

- `BlueprintEnv.render(template, variables=None)`: evaluates a template against the simulated states and returns the value with its real type.
- `BlueprintEnv.last_trace()` and `Trace`: the variables the last run evaluated (`trace.variables`) and the paths it went through (`trace.path`). Raises `LookupError` before the first run. It reads Home Assistant's `trace` component, in one function.
- `start(config_entries=[...])` and `MockConfigEntry`: config entries added before the blueprint starts, for template functions such as `config_entry_attr`.

### Changed

- The automation under test now has an id (`blueprint_under_test`), because Home Assistant stores no trace for an automation without one.

## [0.2.0] - 2026-11-08

Pre-1.0: the dependency change below is the reason for a MINOR version.

Tested with: Home Assistant 2026.11.0, `pytest-homeassistant` 2026.11.0, Python 3.14.10 (macOS) and Ubuntu (CI); also Home Assistant 2026.10.4 with `pytest-homeassistant-custom-component` 0.13.375, Python 3.14.

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
