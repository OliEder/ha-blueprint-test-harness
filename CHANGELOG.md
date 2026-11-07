# Changelog

All notable changes to this project are written here, newest first. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). How versions are chosen is in [`RELEASING.md`](RELEASING.md).

## [Unreleased]

### Added

- `BlueprintEnv` and the `blueprint_env` pytest fixture: load an automation blueprint with `use_blueprint`, set states, fire events, advance a frozen clock, mock services and read the recorded calls.
- `Call`, `sets_state` and `BlueprintLoadError`.
- The mutation tool `python -m ha_blueprint_test_harness.mutate`: structural and Jinja-template mutations, the outcomes killed, survived, invalid and error, and the options `--timeout`, `--workdir` and `--fail-under`.
- `pyproject.toml`, so that the package can be built and installed.
- Licensed under the Apache License 2.0.
