# Getting started

At the end you have run a test against Home Assistant's own `motion_light` blueprint.

## 1. What you need

- **Python 3.14.** The package declares `requires-python >= 3.14`, because the Home Assistant version it is tested with needs it.
- **macOS or Linux.** Tested on macOS and on Ubuntu (GitHub Actions). Windows: not tried.
- About 700 MB of disk for the virtual environment (660 MB measured on macOS on 2026-11-07 with `du -sh .venv`): installing Home Assistant's test package (next step) brings Home Assistant itself.

## 2. Install

Use a virtual environment so that nothing leaks into or out of your other Python projects.

```sh
uv venv --python 3.14 .venv
```

(Without `uv`: `python3.14 -m venv .venv`.)

Then install the harness. Pick one:

| Source | Command | Notes |
| --- | --- | --- |
| A release wheel | `uv pip install --python .venv/bin/python ha_blueprint_test_harness-<version>-py3-none-any.whl` | Download it from the [Releases page](https://github.com/OliEder/ha-blueprint-test-harness/releases). Preferred. |
| The main branch | `uv pip install --python .venv/bin/python "git+https://github.com/OliEder/ha-blueprint-test-harness"` | Installs the development version of `main`. Checked on 2026-11-07. |

It is **not on PyPI yet.**

The harness does not install Home Assistant's test package itself, because there are two and they must not be installed together (the README of `pytest-homeassistant` says so). Install one of them into the same environment:

| Package | Command | Notes |
| --- | --- | --- |
| `pytest-homeassistant` | `uv pip install --python .venv/bin/python pytest-homeassistant` | Recommended. Maintained in Home Assistant core; needs Python 3.14.2 or newer. |
| `pytest-homeassistant-custom-component` | `uv pip install --python .venv/bin/python pytest-homeassistant-custom-component` | The older package, from one maintainer. Use it if you already depend on it. |

Without either, importing the harness fails with "No Home Assistant test package found". Pin the package in your own project if you want repeatable runs, see [Configuring your project](configuring-your-project.md#pin-the-versions).

## 3. Two configuration files

In the folder from which you run `pytest`:

`pytest.ini`

```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
addopts = -p no:respx
```

`-p no:respx` is needed with `pytest-homeassistant` (without it pytest stops at startup with `httpx was already imported`); with the older package it does no harm.

`conftest.py`

```python
# Makes pytest load the harness' fixture (`blueprint_env`) for every test in this project.
pytest_plugins = ["ha_blueprint_test_harness.pytest_plugin"]
```

All of it is needed. Why, and what happens without them, is in [Troubleshooting](troubleshooting.md). If a later test of a blueprint with a `time_pattern` trigger fails with "Lingering timer after test", add the fixture shown under [Configuring your project](configuring-your-project.md#the-two-files-that-must-exist).

## 4. Your first test

Create `tests/test_motion_light.py`. It tests the blueprint that ships with Home Assistant, so you need no blueprint file of your own to try it.

```python
import pathlib

import homeassistant.components.automation as automation

# The blueprint file that ships with Home Assistant.
BLUEPRINT = pathlib.Path(automation.__file__).parent / "blueprints" / "motion_light.yaml"


async def test_the_light_turns_on_with_motion(blueprint_env):
    # Load the blueprint with its inputs, the sensor off, and the two light services replaced by recorders.
    await blueprint_env.start(
        BLUEPRINT,
        {"motion_entity": "binary_sensor.motion", "light_target": {"entity_id": "light.hall"}},
        states={"binary_sensor.motion": "off"},
        services=["light.turn_on", "light.turn_off"],
    )
    # The sensor reports motion; the blueprint must react by switching the light on.
    await blueprint_env.set_state("binary_sensor.motion", "on")
    assert [call.name for call in blueprint_env.calls] == ["light.turn_on"]
```

Run it:

```sh
.venv/bin/python -m pytest
```

Expected: `1 passed`.

What happened: `start()` copied the blueprint into a temporary configuration folder, set up an automation that uses it with your inputs, and replaced `light.turn_on` and `light.turn_off` by recorders. `set_state()` changed the state of the sensor inside the throw-away Home Assistant, the automation ran, and the recorder wrote down the call it made. Nothing outside the test was touched.

## 5. Next

- Test a blueprint of your own, and move the time forward: [Writing tests](writing-tests.md).
- Check that your tests would catch a broken blueprint: [Mutation testing](mutation-testing.md).
- Run all of it on every push: [Configuring your project](configuring-your-project.md#run-it-in-github-actions).
