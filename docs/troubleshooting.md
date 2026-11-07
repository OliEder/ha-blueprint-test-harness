# Troubleshooting

Each entry is an error or symptom with its cause and fix. They were reproduced in a fresh environment on 2026-11-07, except the three mutation-tool messages, which are taken from the tool's own code. If yours is not here, [open an issue](https://github.com/OliEder/ha-blueprint-test-harness/issues) with the output and the versions (`pip show homeassistant pytest-homeassistant-custom-component ha-blueprint-test-harness`).

| Symptom | Cause | Fix |
| --- | --- | --- |
| Every test errors, with `PytestRemovedIn9Warning` ... `sync test depending on async fixture` | pytest-asyncio is not in automatic mode | Add `asyncio_mode = auto` under `[pytest]` in `pytest.ini` |
| `fixture 'blueprint_env' not found` | The plugin is not loaded | Add `pytest_plugins = ["ha_blueprint_test_harness.pytest_plugin"]` to `conftest.py` |
| `-p ha_blueprint_test_harness.pytest_plugin` on the command line fails with `AssertionError: assert 'homeassistant.components.recorder.util' not in ...` | Loading the plugin that early imports Home Assistant too soon for its test setup | Use `conftest.py` as above instead of `-p` |
| `Failed: Lingering timer after test` | The blueprint has a state, `time_pattern` or sun trigger and leaves a timer armed; Home Assistant's test setup fails such a test | Add the `expected_lingering_timers` fixture to `conftest.py` ([Configuring your project](configuring-your-project.md#the-two-files-that-must-exist)) |
| `BlueprintLoadError: the blueprint did not produce a working automation` | The blueprint did not load: a required input is missing, an input name is wrong, or the YAML is invalid | Read the log pytest prints below the failure, for example `Failed to generate automation from blueprint: Missing input light` |
| A test that expects a call sees none, and the log says `Service not found ... Action light.turn_off not found` | The blueprint calls a service you did not list in `services=` | List every service the blueprint can call |
| A test passes but should not | `await` is missing on `set_state`, `fire_event`, `advance` or `settle` (pytest prints `RuntimeWarning: coroutine ... was never awaited`) | Add `await`; a coroutine that is never awaited does nothing |
| A time-based test sees nothing happen | The clock only moves when you call `advance()` | Call `await blueprint_env.advance(seconds)`; see [Writing tests](writing-tests.md#let-time-pass) |
| A test hangs when you call `hass.async_block_till_done()` | A script waiting for a trigger or in a `delay` keeps a task open for ever | Don't call it; the harness's calls settle for you, and `await blueprint_env.settle()` handles long chains |
| `RuntimeError: start() can be called once per environment` | `start()` was called twice in one test | One `start()` per test; use a helper to start the blueprint the same way in each test |
| Mutation tool: `The tests do not pass on the unmodified blueprint` | Your tests fail before anything is broken | Run the test command without the tool and fix it |
| Mutation tool: `The tests fail on the unmodified blueprint after a YAML round trip` | The tool wrote the blueprint back differently in a way your tests notice | [Open an issue](https://github.com/OliEder/ha-blueprint-test-harness/issues) with the blueprint (without private entity names) |
| Mutation tool: `error` outcomes | The test command itself broke, for example a wrong path or no tests collected | Run the exact command after `--` by hand |
| Installing fails or picks a surprising Home Assistant | Wrong Python, or a newer test package than the one tested | Use Python 3.14 and pin `pytest-homeassistant-custom-component` ([Configuring your project](configuring-your-project.md#pin-the-versions)) |
| `pytest` fails on a plugin that has nothing to do with this project | Another package in the same environment brings a broken pytest plugin (seen with the machine's global Python) | Use a virtual environment of its own |

## Reading the log of a failing test

pytest prints Home Assistant's log under a failing test (the section "Captured log call"). Look there first: Home Assistant logs a bad blueprint and carries on instead of failing, which is why the harness turns that into `BlueprintLoadError` and why a missing service shows up only in the log.

## Using something newer than what was tested

Home Assistant releases every month. This project was tested with Home Assistant 2026.10.4. The harness uses internals of Home Assistant in several places, so a newer version can break it without warning. If it does, please open an issue with the two version numbers.
