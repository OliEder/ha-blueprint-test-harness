"""Documentation example: moving time forward with advance(), on Home Assistant's own motion_light blueprint."""

import pathlib

import homeassistant.components.automation as automation

BLUEPRINT = pathlib.Path(automation.__file__).parent / "blueprints" / "motion_light.yaml"
INPUTS = {"motion_entity": "binary_sensor.motion", "light_target": {"entity_id": "light.hall"}}


# Loads the blueprint with the sensor off and recorders for the two light services.
async def start(env, **extra_inputs):
    await env.start(BLUEPRINT, {**INPUTS, **extra_inputs}, states={"binary_sensor.motion": "off"},
                    services=["light.turn_on", "light.turn_off"])


async def test_the_light_goes_off_after_the_wait_time(blueprint_env):
    # Motion starts and stops; the blueprint waits 120 seconds (its default) before it switches the light off.
    await start(blueprint_env)
    await blueprint_env.set_state("binary_sensor.motion", "on")
    await blueprint_env.set_state("binary_sensor.motion", "off")
    await blueprint_env.advance(119)
    assert [call.name for call in blueprint_env.calls] == ["light.turn_on"]  # one second too early
    await blueprint_env.advance(1)
    assert [call.name for call in blueprint_env.calls] == ["light.turn_on", "light.turn_off"]


async def test_a_shorter_wait_time_is_honoured(blueprint_env):
    # The input `no_motion_wait` (seconds) changes how long the blueprint waits.
    await start(blueprint_env, no_motion_wait=10)
    await blueprint_env.set_state("binary_sensor.motion", "on")
    await blueprint_env.set_state("binary_sensor.motion", "off")
    await blueprint_env.advance(10)
    assert [call.name for call in blueprint_env.calls] == ["light.turn_on", "light.turn_off"]
