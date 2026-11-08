# Troubleshooting

Each entry is an error or symptom with its cause and fix. They were reproduced in a fresh environment on 2026-11-07, except the mutation-tool messages and the `error` outcome, which are taken from the tool's own code. If yours is not here, [open an issue](https://github.com/OliEder/ha-blueprint-test-harness/issues) with the output and the versions (`pip list | grep -i "homeassistant\|ha-blueprint"`).

| Symptom | Cause | Fix |
| --- | --- | --- |
| Every test errors, with `PytestRemovedIn9Warning` ... `sync test depending on async fixture` | pytest-asyncio is not in automatic mode | Add `asyncio_mode = auto` under `[pytest]` in `pytest.ini` |
| `fixture 'blueprint_env' not found` | The plugin is not loaded | Add `pytest_plugins = ["ha_blueprint_test_harness.pytest_plugin"]` to `conftest.py` |
| `-p ha_blueprint_test_harness.pytest_plugin` on the command line fails with `AssertionError: assert 'homeassistant.components.recorder.util' not in ...` | Loading the plugin that early imports Home Assistant too soon for its test setup | Use `conftest.py` as above instead of `-p` |
| `Failed: Lingering timer after test` | The blueprint leaves a timer armed (a `time_pattern` trigger does, for example; Home Assistant's own `motion_light` does not); Home Assistant's test setup fails such a test | Add the `expected_lingering_timers` fixture to `conftest.py` ([Configuring your project](configuring-your-project.md#the-two-files-that-must-exist)) |
| `BlueprintLoadError: the blueprint did not produce a working automation` | The blueprint did not load: a required input is missing, or the YAML is invalid (a misspelled *optional* input is not reported at all, see [Writing tests](writing-tests.md#things-that-surprise-people)) | Read the log pytest prints below the failure, for example `Failed to generate automation from blueprint: Missing input light` |
| A test that expects a call sees none, and the log says `Service not found ... Action light.turn_off not found` | The blueprint calls a service you did not list in `services=` | List every service the blueprint can call |
| A test passes but should not | `await` is missing on `set_state`, `fire_event`, `advance` or `settle` (pytest prints `RuntimeWarning: coroutine ... was never awaited`) | Add `await`; a coroutine that is never awaited does nothing |
| A time-based test sees nothing happen | The clock only moves when you call `advance()` | Call `await blueprint_env.advance(seconds)`; see [Writing tests](writing-tests.md#let-time-pass) |
| A test hangs when you call `hass.async_block_till_done()` | A script waiting for a trigger or in a `delay` keeps a task open for ever | Don't call it; the harness's calls settle for you, and `await blueprint_env.settle()` handles long chains |
| `RuntimeError: start() can be called once per environment` | `start()` was called twice in one test | One `start()` per test; use a helper to start the blueprint the same way in each test |
| Mutation tool: `The tests do not pass on the unmodified blueprint` | Your tests fail before anything is broken | Run the test command without the tool and fix it |
| Mutation tool: `The tests fail on the unmodified blueprint after a YAML round trip` | The tool wrote the blueprint back differently in a way your tests notice | [Open an issue](https://github.com/OliEder/ha-blueprint-test-harness/issues) with the blueprint (without private entity names) |
| Mutation tool: `Cannot run the test command ...` (exit 1) | The program after `--` cannot be started, for example a wrong path to Python | Run the exact command after `--` by hand |
| Mutation tool: `error` outcome for single mutants | The tests passed on the original, but the test run exited with a code of 2 or more on a mutant (pytest itself broke, for example a timeout of the machine) | Keep the mutant files with `--workdir DIR` and run the tests against that file by hand |
| `ImportError: No Home Assistant test package found` | Neither `pytest-homeassistant` nor `pytest-homeassistant-custom-component` is installed | Install one of them ([Getting started](getting-started.md#2-install)) |
| pytest stops at startup with `RuntimeError: httpx was already imported; call alias_httpx() before any import httpx` | `pytest-homeassistant` is installed and the `respx` plugin loads first | Add `addopts = -p no:respx` under `[pytest]` in `pytest.ini` |
| Odd failures after installing the second test package | `pytest-homeassistant` and `pytest-homeassistant-custom-component` must not be installed together. `uv pip install --dry-run` (2026-11-08) reports no conflict: it swaps Home Assistant 2026.11.0 for 2026.10.4 and keeps both test packages | Create a fresh environment and install one of them |
| Installing fails or picks a surprising Home Assistant | Wrong Python (`pytest-homeassistant` needs 3.14.2 or newer), or a newer test package than the one tested | Use Python 3.14 and pin the test package ([Configuring your project](configuring-your-project.md#pin-the-versions)) |
| `pytest` fails on a plugin that has nothing to do with this project | Another package in the same environment brings a broken pytest plugin (seen with the machine's global Python) | Use a virtual environment of its own |

## Reading the log of a failing test

pytest prints Home Assistant's log under a failing test (the section "Captured log call"). Look there first: Home Assistant logs a bad blueprint and carries on instead of failing, which is why the harness turns that into `BlueprintLoadError` and why a missing service shows up only in the log.

## Using something newer than what was tested

Home Assistant releases every month. This project was tested with Home Assistant 2026.10.4. The harness uses internals of Home Assistant in several places, so a newer version can break it without warning. If it does, please open an issue with the two version numbers.
