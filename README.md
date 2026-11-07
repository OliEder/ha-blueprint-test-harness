# ha-blueprint-test-harness

Run a Home Assistant **automation blueprint** in-process: load the real YAML with `use_blueprint`, set states, advance a frozen clock, and assert which services it called. Pre-1.0: the API may still change, see [`RELEASING.md`](RELEASING.md). Not an official Home Assistant project.

```python
async def test_light_turns_off_after_the_wait(blueprint_env):
    await blueprint_env.start("motion_light.yaml",
        {"motion_entity": "binary_sensor.motion", "light_target": {"entity_id": "light.hall"}},
        states={"binary_sensor.motion": "off"}, services=["light.turn_on", "light.turn_off"])
    await blueprint_env.set_state("binary_sensor.motion", "on")
    await blueprint_env.set_state("binary_sensor.motion", "off")
    await blueprint_env.advance(120)
    assert [call.name for call in blueprint_env.calls] == ["light.turn_on", "light.turn_off"]
```

## Documentation

Everything needed to use it is in [`docs/`](docs/index.md): [getting started](docs/getting-started.md) (install, two configuration files, a first test), [configuring your project](docs/configuring-your-project.md) (layout, pinned versions, GitHub Actions), [writing tests](docs/writing-tests.md) (the API and the common patterns), [mutation testing](docs/mutation-testing.md) and [troubleshooting](docs/troubleshooting.md).

Needs Python 3.14. Install a release wheel from the [Releases page](https://github.com/OliEder/ha-blueprint-test-harness/releases) or, until then, `pip install "git+https://github.com/OliEder/ha-blueprint-test-harness"`. It is not on PyPI yet.

## What is real, what is not

| Real | Not real |
|---|---|
| Blueprint loading and input validation | Every service in `services=` (recorded, never executed, any data accepted) |
| Templates, triggers, conditions, `wait_for_trigger`, `delay`, `mode:` | All integrations and devices |
| The state machine (`last_changed`, `last_reported`) | Service schemas of real integrations (a changed parameter goes unnoticed) |
| Time: a frozen clock you advance with `advance()` | Anything on a real instance |

A green run says the blueprint logic does what the test describes under these assumptions. It says nothing about a real device.

Only automation blueprints are supported. The API and the patterns are in [Writing tests](docs/writing-tests.md).

## Develop this project

```
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python -m pytest
```

`requirements-dev.txt` pins `pytest-homeassistant-custom-component==0.13.375` (Home Assistant 2026.10.4). The helpers it uses are internal to Home Assistant and can change between versions.

## CI

`.github/workflows/ci.yaml` runs two jobs on Linux with Python 3.14: `tests` (the project's own tests) and `mutation` (mutation runs on Home Assistant's `motion_light.yaml` and on the fixture `tests/blueprints/daylight_heartbeat.yaml`, each with `--fail-under 100`; survivors go into the job summary). `.github/workflows/release.yaml` builds a release from a version tag; see [`RELEASING.md`](RELEASING.md).

## Tests

- `tests/test_motion_light.py`: Home Assistant's own `motion_light.yaml`, unchanged.
- `tests/test_daylight_heartbeat.py`: a small original blueprint (`tests/blueprints/daylight_heartbeat.yaml`) that needs a time pattern, sun conditions and a `choose` block.
- `docs/examples/`: the blueprint and the tests that the documentation quotes; they run with the rest of the suite.
- `tests/test_mutate.py`: the mutation tool itself.
- `tests/test_memory.py`, `tests/test_status.py`, `tests/test_roadmap.py`, `tests/test_release.py`: check that the project's own documents agree with each other and with the code.

## Versions and releases

Version numbers, what counts as a breaking change and the release steps are in [`RELEASING.md`](RELEASING.md); what changed in each version is in [`CHANGELOG.md`](CHANGELOG.md).

## Mutation testing

Do the tests notice when the blueprint is broken? The tool changes the YAML one small thing at a time and runs your tests against each change:

```
python -m ha_blueprint_test_harness.mutate path/to/blueprint.yaml [--timeout S] [--fail-under PCT] -- python -m pytest -q -x tests/test_my_blueprint.py
```

A survivor is a test that is missing, or a change that does not alter behaviour. On Home Assistant's `motion_light.yaml` the first run killed 16 of 18 mutants; the two survivors showed that nothing tested a sensor that drops out while the light is on. The outcomes, the operators, reading survivors and CI use are in [Mutation testing](docs/mutation-testing.md).

## License

Apache License 2.0, see [`LICENSE`](LICENSE).

## Prior work and credits

- **MrCodeLabs.** This project started from the blueprint tests that [MrCodeLabs](https://github.com/MrCodeLabs) wrote for the go-eCharger PV blueprint of the [ha-goecharger-api2](https://github.com/marq24/ha-goecharger-api2) integration (`tests/blueprints/` on the branch `feat/pv-freshness-confirmation` of [his fork](https://github.com/MrCodeLabs/ha-goecharger-api2), Apache-2.0). His idea, to run a blueprint's real templates and actions against synthetic states and assert on the service calls, and several of his first scenarios (a daylight value, unusable measurements, a night window, routing to a chosen target) shaped this project. His harness rebuilds parts of Home Assistant in a Jinja sandbox; this project runs the blueprint in a real Home Assistant and adds time control, a mutation tool and CI. The code in this repository was written from scratch; nothing was copied from his files.
- **Home Assistant.** Loading a blueprint with `use_blueprint` and counting mocked service calls follows the pattern of Home Assistant's own [`tests/components/automation/test_blueprint.py`](https://github.com/home-assistant/core/blob/dev/tests/components/automation/test_blueprint.py). The harness is built on [`pytest-homeassistant-custom-component`](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) (MIT).
