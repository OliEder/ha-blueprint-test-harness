"""Home Assistant's own motion_light blueprint, unchanged, as the first user of the harness."""

import pathlib

import homeassistant.components.automation as automation
import pytest

from ha_blueprint_test_harness import sets_state

BLUEPRINT = pathlib.Path(automation.__file__).parent / "blueprints" / "motion_light.yaml"
MOTION, LIGHT = "binary_sensor.motion", "light.hall"
INPUTS = {"motion_entity": MOTION, "light_target": {"entity_id": LIGHT}}
SERVICES = ("light.turn_on", "light.turn_off")


async def start(env, wait=None, motion="off", effects=None):
    # Loads the motion_light blueprint with the standard inputs; optionally another wait time, a starting motion state and service effects.
    inputs = INPUTS if wait is None else {**INPUTS, "no_motion_wait": wait}
    await env.start(BLUEPRINT, inputs, states={MOTION: motion, LIGHT: "off"}, services=SERVICES, effects=effects)


def names(env):
    # The names of all service calls so far, in order, to keep the assertions short.
    return [call.name for call in env.calls]


async def test_motion_turns_the_light_on(blueprint_env):
    # Motion starting must make the blueprint call light.turn_on on our light, and nothing else.
    await start(blueprint_env)
    await blueprint_env.set_state(MOTION, "on")
    assert names(blueprint_env) == ["light.turn_on"]
    assert blueprint_env.calls[0].entity_ids == {LIGHT}


async def test_light_stays_on_while_motion_continues(blueprint_env):
    # While the sensor stays 'on' the light is never turned off, even after an hour.
    await start(blueprint_env)
    await blueprint_env.set_state(MOTION, "on")
    await blueprint_env.advance(3600)
    assert names(blueprint_env) == ["light.turn_on"]


@pytest.mark.parametrize("wait", [None, 30, 600])
async def test_light_turns_off_exactly_after_the_wait(blueprint_env, wait):
    # After motion stops, light.turn_off comes exactly after the wait (120 s by default), not one second earlier.
    await start(blueprint_env, wait)
    seconds = 120 if wait is None else wait
    await blueprint_env.set_state(MOTION, "on")
    await blueprint_env.set_state(MOTION, "off")
    await blueprint_env.advance(seconds - 1)
    assert names(blueprint_env) == ["light.turn_on"]
    await blueprint_env.advance(1)
    assert names(blueprint_env) == ["light.turn_on", "light.turn_off"]
    assert blueprint_env.calls[1].entity_ids == {LIGHT}


async def test_zero_wait_turns_off_at_once(blueprint_env):
    # With a wait of 0 the light goes off as soon as motion stops.
    await start(blueprint_env, 0)
    await blueprint_env.set_state(MOTION, "on")
    await blueprint_env.set_state(MOTION, "off")
    assert names(blueprint_env) == ["light.turn_on", "light.turn_off"]


async def test_new_motion_restarts_the_wait(blueprint_env):
    # New motion during the countdown restarts it: the old timer must not turn the light off.
    await start(blueprint_env)
    await blueprint_env.set_state(MOTION, "on")
    await blueprint_env.set_state(MOTION, "off")
    await blueprint_env.advance(100)
    await blueprint_env.set_state(MOTION, "on")      # run restarts, the old 120 s timer is gone
    await blueprint_env.advance(50)                  # 150 s after the first motion ended
    assert "light.turn_off" not in names(blueprint_env)
    await blueprint_env.set_state(MOTION, "off")
    await blueprint_env.advance(119)
    assert "light.turn_off" not in names(blueprint_env)
    await blueprint_env.advance(1)
    assert names(blueprint_env) == ["light.turn_on", "light.turn_on", "light.turn_off"]


async def test_unavailable_sensor_coming_back_as_on_does_not_trigger(blueprint_env):
    # The trigger needs 'off' -> 'on', so 'unavailable' -> 'on' must not turn the light on.
    await start(blueprint_env)
    await blueprint_env.set_state(MOTION, "unavailable")
    await blueprint_env.set_state(MOTION, "on")      # trigger needs from: "off"
    await blueprint_env.advance(3600)
    assert blueprint_env.calls == []


async def test_motion_already_on_at_start_does_nothing(blueprint_env):
    # A sensor that is already 'on' when the automation starts is not new motion.
    await start(blueprint_env, motion="on")
    await blueprint_env.advance(3600)
    assert blueprint_env.calls == []


async def test_simulated_light_follows_the_calls(blueprint_env):
    # With effects the simulated light really switches on and off, so checks on the light's state work too.
    effects = {"light.turn_on": sets_state("on"), "light.turn_off": sets_state("off")}
    await start(blueprint_env, 10, effects=effects)
    await blueprint_env.set_state(MOTION, "on")
    assert blueprint_env.hass.states.get(LIGHT).state == "on"
    await blueprint_env.set_state(MOTION, "off")
    await blueprint_env.advance(10)
    assert blueprint_env.hass.states.get(LIGHT).state == "off"


# The next two pin down the blueprint as shipped: only a real "on" -> "off" change ends the wait, so a
# sensor dropout leaves the light on until there is new motion. Whether that is desirable is a separate question.
async def test_sensor_dropping_out_while_on_does_not_start_the_countdown(blueprint_env):
    # Sensor goes 'on' -> 'unavailable': the countdown must not start, the light stays on.
    await start(blueprint_env)
    await blueprint_env.set_state(MOTION, "on")
    await blueprint_env.set_state(MOTION, "unavailable")
    await blueprint_env.advance(3600)
    assert names(blueprint_env) == ["light.turn_on"]


async def test_recovering_as_off_after_a_dropout_does_not_start_the_countdown(blueprint_env):
    # Sensor comes back as 'off' after a dropout: still no countdown, because it did not change from 'on'.
    await start(blueprint_env)
    await blueprint_env.set_state(MOTION, "on")
    await blueprint_env.set_state(MOTION, "unavailable")
    await blueprint_env.set_state(MOTION, "off")
    await blueprint_env.advance(3600)
    assert names(blueprint_env) == ["light.turn_on"]
