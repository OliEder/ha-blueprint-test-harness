"""Documentation example: tests for button_light.yaml, a blueprint that toggles a light on an event.

Shows fire_event, an effect that lets the mocked light change state, and calls_to.
"""

import pathlib

import pytest

from ha_blueprint_test_harness import BlueprintLoadError, sets_state

BLUEPRINT = pathlib.Path(__file__).parent / "button_light.yaml"
LIGHT = "light.desk"


# Loads the blueprint with the light switched off. The mocked services change the light's state, like real ones would.
async def start(env, light_state="off", **inputs):
    await env.start(
        BLUEPRINT,
        {"light": LIGHT, **inputs},
        states={LIGHT: light_state},
        services=["light.turn_on", "light.turn_off"],
        effects={"light.turn_on": sets_state("on"), "light.turn_off": sets_state("off")},
    )


# The names of all service calls so far, in order.
def names(env):
    return [call.name for call in env.calls]


async def test_a_press_turns_an_off_light_on(blueprint_env):
    # The light is off, so the press must switch it on and do nothing else.
    await start(blueprint_env)
    await blueprint_env.fire_event("button_pressed")
    assert names(blueprint_env) == ["light.turn_on"]
    assert blueprint_env.calls[0].entity_ids == {LIGHT}


async def test_a_second_press_turns_it_off_again(blueprint_env):
    # The effect switched the simulated light on, so the second press must switch it off.
    await start(blueprint_env)
    await blueprint_env.fire_event("button_pressed")
    await blueprint_env.fire_event("button_pressed")
    assert names(blueprint_env) == ["light.turn_on", "light.turn_off"]
    # Both calls must be aimed at our light; a call without a target would switch off nothing.
    assert [call.entity_ids for call in blueprint_env.calls] == [{LIGHT}, {LIGHT}]


async def test_a_light_that_is_already_on_is_turned_off(blueprint_env):
    # Starting with the light on, the first press switches it off.
    await start(blueprint_env, light_state="on")
    await blueprint_env.fire_event("button_pressed")
    assert names(blueprint_env) == ["light.turn_off"]


async def test_other_events_are_ignored(blueprint_env):
    # Only the configured event counts.
    await start(blueprint_env)
    await blueprint_env.fire_event("something_else")
    assert blueprint_env.calls == []


async def test_the_event_type_can_be_changed_by_an_input(blueprint_env):
    # With another event type configured, the default event no longer works and the new one does.
    await start(blueprint_env, button_event="doorbell")
    await blueprint_env.fire_event("button_pressed")
    assert blueprint_env.calls == []
    await blueprint_env.fire_event("doorbell")
    assert names(blueprint_env) == ["light.turn_on"]


async def test_a_missing_required_input_is_reported(blueprint_env):
    # A blueprint that cannot load is reported as BlueprintLoadError, not as a silent test pass.
    with pytest.raises(BlueprintLoadError):
        await blueprint_env.start(BLUEPRINT, {}, services=["light.turn_on"])
