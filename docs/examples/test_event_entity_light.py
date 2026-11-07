"""Documentation example: simulating presses of a button that is an event entity (such as a Zigbee2MQTT button)."""

import itertools
import pathlib

BLUEPRINT = pathlib.Path(__file__).parent / "event_entity_light.yaml"
BUTTON, LIGHT = "event.hall_button_action", "light.hall"

# A real event entity gets a new timestamp as its state on every press; this counter makes one.
_presses = itertools.count()


# Loads the blueprint with the button in a state that does not count as a press ("unknown", like after a restart).
async def start(env):
    await env.start(BLUEPRINT, {"button": BUTTON, "light": LIGHT}, states={BUTTON: "unknown"},
                    services=["light.turn_on", "light.turn_off"])


# Simulates one press: a new timestamp as the state and the kind of press in the attribute `event_type`.
async def press(env, event_type):
    stamp = f"2026-01-01T10:00:{next(_presses):02d}.000+00:00"
    await env.set_state(BUTTON, stamp, {"event_type": event_type})


# The names of all service calls so far.
def names(env):
    return [call.name for call in env.calls]


async def test_each_kind_of_press_does_its_own_thing(blueprint_env):
    # single_up switches the light on, single_down off; the order of the calls follows the order of the presses.
    await start(blueprint_env)
    await press(blueprint_env, "single_up")
    await press(blueprint_env, "single_down")
    assert names(blueprint_env) == ["light.turn_on", "light.turn_off"]
    # Both calls must be aimed at our light; a call without a target would switch off nothing.
    assert [call.entity_ids for call in blueprint_env.calls] == [{LIGHT}, {LIGHT}]


async def test_the_same_press_twice_counts_twice_with_a_new_timestamp(blueprint_env):
    # Two presses of the same kind are two events because each has its own timestamp.
    await start(blueprint_env)
    await press(blueprint_env, "single_up")
    await press(blueprint_env, "single_up")
    assert names(blueprint_env) == ["light.turn_on", "light.turn_on"]


async def test_the_same_state_again_is_not_a_press(blueprint_env):
    # A state trigger fires on a changed state. Writing the same timestamp again, even with another event_type, is
    # not a new press, so a test that forgets the new timestamp sees nothing and may pass for the wrong reason.
    await start(blueprint_env)
    await blueprint_env.set_state(BUTTON, "2026-01-01T10:00:00.000+00:00", {"event_type": "single_up"})
    await blueprint_env.set_state(BUTTON, "2026-01-01T10:00:00.000+00:00", {"event_type": "single_down"})
    assert names(blueprint_env) == ["light.turn_on"]


async def test_an_event_type_that_nobody_listens_to_does_nothing(blueprint_env):
    # A kind of press the blueprint does not handle must not call any service.
    await start(blueprint_env)
    await press(blueprint_env, "hold_up")
    assert blueprint_env.calls == []


async def test_the_unavailable_state_is_ignored(blueprint_env):
    # When the device goes away or comes back the entity becomes unavailable; that is not a press.
    await start(blueprint_env)
    await blueprint_env.set_state(BUTTON, "unavailable", {"event_type": "single_up"})
    assert blueprint_env.calls == []
