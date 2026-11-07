# Writing tests

How a test is built, the whole API, and the patterns you will use most. The examples on this page are in [`examples/`](examples/), run with the project's test suite.

## The shape of every test

```python
async def test_something(blueprint_env):
    await blueprint_env.start(BLUEPRINT, inputs, states=..., services=...)   # 1. load the blueprint, once
    await blueprint_env.set_state("binary_sensor.motion", "on")                # 2. make something happen
    assert [call.name for call in blueprint_env.calls] == ["light.turn_on"]    # 3. look at what it did
```

1. **Arrange.** `start()` loads the blueprint as a real automation inside a throw-away Home Assistant. Call it once per test (a second call raises `RuntimeError`).
2. **Act.** Change a state, fire an event or let time pass. Each call lets the blueprint react before it returns.
3. **Assert.** `calls` lists every service call the blueprint made, in order.

The fixture `blueprint_env` gives every test a fresh Home Assistant, an empty configuration folder and a clock that stands still until you move it.

## `start()`

```python
await blueprint_env.start(
    blueprint, inputs=None, *,
    states=None, services=(), effects=None, components=(), when=None, alias="blueprint under test",
)
```

| Parameter | What it is |
| --- | --- |
| `blueprint` | Path to the blueprint file (a `str` or a `pathlib.Path`). |
| `inputs` | A dict of the blueprint's inputs, as you would fill them in the UI: `{"motion_entity": "binary_sensor.motion", "light_target": {"entity_id": "light.hall"}}`. Inputs with a default can be left out. |
| `states` | The starting states: `{"binary_sensor.motion": "off"}`. With attributes, give a pair: `{"sensor.power": ("1200", {"unit_of_measurement": "W"})}`. Set before the automation is created. |
| `services` | The services to replace by recorders, as `"domain.service"` names: `["light.turn_on", "light.turn_off"]`. A service the blueprint calls that is **not** listed is not recorded: Home Assistant logs `Service not found ... Action light.turn_off not found` and the test does **not** fail by itself. List every service your blueprint can call. |
| `effects` | Optional: what a recorded service does besides recording. `{"light.turn_on": sets_state("on")}` puts the targeted lights into the state `on`, so a later condition sees a light that is on. You may write your own: a function `f(hass, call)`, plain or `async`. |
| `components` | Real Home Assistant components to set up first, for example `["sun"]` for sunrise and sunset conditions. |
| `when` | A timezone-aware `datetime` to move the clock to before anything runs, for example `dt.datetime(2026, 6, 21, 20, 0, tzinfo=dt.UTC)`. |
| `alias` | The automation's name. Rarely needed. |

If the blueprint does not turn into a working automation (a missing required input, invalid YAML), `start()` raises **`BlueprintLoadError`**. The reason is in the log that pytest prints with the failure, for example `Failed to generate automation from blueprint: Missing input light`.

## Acting on the blueprint

| Call | What it does |
| --- | --- |
| `await set_state(entity_id, state, attributes=None)` | Writes a state, like a device reporting a new value, and lets the blueprint react. |
| `await fire_event(event_type, data=None)` | Fires an event on Home Assistant's event bus, for example a button press, and lets the blueprint react. |
| `await advance(seconds)` | Moves the frozen clock forward and runs every timer that is due: `delay`, `for:` durations, `time_pattern` triggers. Nobody waits for real. |
| `await settle()` | Lets everything that is ready run. The calls above do this for you; you need it only after a very long chain of actions. |

## Looking at the result

| Name | What it gives |
| --- | --- |
| `calls` | A list of every recorded service call, in the order they happened. |
| `calls_to("light.turn_off")` | The same, for one service. |
| `call.name` | `"light.turn_on"`. |
| `call.data` | The call's data as a dict, for example `{"entity_id": ["light.hall"], "brightness_pct": 50}`. |
| `call.entity_ids` | The targeted entities as a set, whether the blueprint passed a string or a list. |
| `hass` | The Home Assistant instance, for anything the API does not cover (for example `hass.states.get(...)`). Internals can change between Home Assistant versions. |

## Patterns

### React to an event, and let a service change a state

[`examples/button_light.yaml`](examples/button_light.yaml) toggles a light when an event fires. The test uses `fire_event`, and `effects` so that the simulated light really turns on and the second press can turn it off:

```python
await blueprint_env.start(
    BLUEPRINT, {"light": "light.desk"}, states={"light.desk": "off"},
    services=["light.turn_on", "light.turn_off"],
    effects={"light.turn_on": sets_state("on"), "light.turn_off": sets_state("off")},
)
await blueprint_env.fire_event("button_pressed")
await blueprint_env.fire_event("button_pressed")
assert [call.name for call in blueprint_env.calls] == ["light.turn_on", "light.turn_off"]
```

Without `effects` the light would stay `off` and the second press would switch it on again. The full tests, including one for an unrelated event and one for an input that changes the event type, are in [`examples/test_button_light.py`](examples/test_button_light.py).

### Let time pass

[`examples/test_motion_light_timing.py`](examples/test_motion_light_timing.py) checks that Home Assistant's `motion_light` blueprint switches the light off after its wait time, and not a second earlier:

```python
await blueprint_env.set_state("binary_sensor.motion", "on")
await blueprint_env.set_state("binary_sensor.motion", "off")
await blueprint_env.advance(119)       # nothing yet
await blueprint_env.advance(1)         # now the light goes off
```

Advance in steps if the blueprint does something every few seconds (`time_pattern`): call `advance(5)` several times and look at `calls` in between.

### Times of day, sun conditions and numbers

`when=` starts the clock at a moment you choose, and `components=["sun"]` sets up the real sun component, so `sunrise` and `sunset` conditions work. Home Assistant's test setup uses the time zone US/Pacific (the fixture tests rely on it); pick times accordingly. A complete example with a `time_pattern` trigger, sun conditions, a `choose` block and numbers is the fixture blueprint `tests/blueprints/daylight_heartbeat.yaml` with its tests in `tests/test_daylight_heartbeat.py` (in the repository, not in the package).

### Assert that nothing happened

A test that only checks that a call happened misses a blueprint that calls too much. Check the whole list:

```python
assert blueprint_env.calls == []                                   # nothing at all
assert [call.name for call in blueprint_env.calls] == ["light.turn_on"]   # exactly this, nothing else
assert blueprint_env.calls[0].entity_ids == {"light.hall"}         # and aimed at the right thing
```

Check the **target** as well as the name. A call without a target switches off nothing and still has the right name; the [mutation tool](mutation-testing.md) finds tests that forget this.

### A blueprint that must not load

```python
import pytest
from ha_blueprint_test_harness import BlueprintLoadError

with pytest.raises(BlueprintLoadError):
    await blueprint_env.start(BLUEPRINT, {}, services=["light.turn_on"])   # a required input is missing
```

## What is simulated and what is not

| Real | Not real |
| --- | --- |
| Blueprint loading and input validation | Every service in `services=` (recorded, never executed, any data accepted) |
| Templates, triggers, conditions, `wait_for_trigger`, `delay`, `mode:` | All integrations and devices |
| The state machine (`last_changed`, `last_reported`) | The service schemas of real integrations (a parameter that a real integration would reject goes unnoticed) |
| Time: a frozen clock you advance with `advance()` | Anything on a real instance |

A green test says that the blueprint's logic does what the test describes, under these assumptions. It says nothing about a real device.

## Things that surprise people

- **Always `await` the calls.** `set_state`, `fire_event`, `advance` and `settle` are coroutines; without `await` nothing happens and the test passes for the wrong reason.
- **A misspelled optional input is ignored.** `start()` does not complain about an input name the blueprint does not have, so the test runs with the default and can pass for the wrong reason. Check input names against the blueprint's `input:` section.
- **A service you forgot to list fails silently.** The action logs an error, `calls` stays empty, and a test that asserts `calls == []` passes for the wrong reason. If a test that should see a call sees none, read the log that pytest prints for `Service not found`.
- **One `start()` per test.** Build a small helper (like `start(env, ...)` in the examples) so that every test loads the blueprint the same way.
- **The clock does not run.** Time only moves when you call `advance()` (or give `when=`). A `delay: 120` is passed by `advance(120)`.
- **Don't call `hass.async_block_till_done()`.** It never returns while a script waits for a trigger or sits in a `delay`. The harness lets the event loop run 20 iterations instead, as Home Assistant's own tests do. A very long chain of actions may need another `await settle()`.
- **Only automation blueprints.** Script and template blueprints are not implemented.
