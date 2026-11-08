"""Reference automation tests: button_scenes.yaml, a button that is an event entity with three kinds of press.

Covers state triggers on an attribute with `from:` lists, trigger ids that select a `choose` branch, and targets by area
(the harness records the data of the call, so an area target is checked in `call.data`, not in `entity_ids`).
"""

import itertools
import pathlib

import pytest

AUTOMATION = pathlib.Path(__file__).parent / "automations" / "button_scenes.yaml"
BUTTON = "event.hall_button"
SERVICES = ["light.toggle", "light.turn_off", "media_player.turn_off"]

# A real event entity gets a new timestamp as its state on every press; this counter makes one.
_presses = itertools.count()


# Starts the automation with the button in a state that does not count as a press.
async def start(env):
    await env.start_automation(AUTOMATION, states={BUTTON: ("unknown", {"event_type": None})}, services=SERVICES)


# One event of the button: a new timestamp as the state and the kind in the attribute `event_type`.
async def event(env, event_type):
    await env.set_state(BUTTON, f"2026-01-01T10:00:{next(_presses):02d}.000+00:00", {"event_type": event_type})


# A press as the device reports it: down, up, then the kind of press (the way a Shelly input does it).
async def press(env, kind):
    await event(env, "btn_down")
    await event(env, "btn_up")
    await event(env, kind)


# The names of all service calls so far.
def names(env):
    return [call.name for call in env.calls]


async def test_one_press_toggles_the_two_spots(blueprint_env):
    await start(blueprint_env)
    await press(blueprint_env, "single_push")
    assert names(blueprint_env) == ["light.toggle"]
    call = blueprint_env.calls[0]
    assert call.entity_ids == {"light.hall_spot_1", "light.hall_spot_2"} and call.data["transition"] == 1
    assert "brightness_pct" not in call.data


async def test_two_presses_toggle_the_other_lights_at_full_brightness(blueprint_env):
    await start(blueprint_env)
    await press(blueprint_env, "double_push")
    call = blueprint_env.calls[0]
    assert names(blueprint_env) == ["light.toggle"]
    assert call.entity_ids == {"light.hall_ceiling", "light.hall_strip"} and call.data["brightness_pct"] == 100


async def test_three_presses_switch_off_the_areas_and_the_tv(blueprint_env):
    await start(blueprint_env)
    await press(blueprint_env, "triple_push")
    assert names(blueprint_env) == ["light.turn_off", "media_player.turn_off"]
    assert blueprint_env.calls[0].data["area_id"] == ["living_room", "kitchen", "bathroom"] and blueprint_env.calls[0].data["transition"] == 1
    assert blueprint_env.calls[1].data["area_id"] == ["living_room"]   # Home Assistant turns a single area into a list


async def test_a_long_press_does_nothing(blueprint_env):
    await start(blueprint_env)
    await press(blueprint_env, "long_push")
    assert blueprint_env.calls == []


async def test_the_press_down_and_up_alone_do_nothing(blueprint_env):
    await start(blueprint_env)
    await event(blueprint_env, "btn_down")
    await event(blueprint_env, "btn_up")
    assert blueprint_env.calls == []


async def test_each_kind_of_press_runs_only_its_own_branch(blueprint_env):
    await start(blueprint_env)
    await press(blueprint_env, "single_push")
    assert "action/0/choose/0/sequence/0" in blueprint_env.last_trace().path
    assert not any("choose/1" in step or "choose/2" in step for step in blueprint_env.last_trace().path if "sequence" in step)


async def test_the_same_kind_twice_in_a_row_counts_once(blueprint_env):
    # Known property of an attribute trigger with `from:`: the second single_push has the same event_type as the
    # first, so nothing changes. It only works because a real device reports btn_down and btn_up in between.
    await start(blueprint_env)
    await press(blueprint_env, "single_push")
    await event(blueprint_env, "single_push")
    assert names(blueprint_env) == ["light.toggle"]


async def test_a_press_after_the_down_and_up_events_counts_again(blueprint_env):
    await start(blueprint_env)
    await press(blueprint_env, "single_push")
    await press(blueprint_env, "single_push")
    assert names(blueprint_env) == ["light.toggle", "light.toggle"]


async def test_changing_from_one_kind_to_another_directly_works(blueprint_env):
    await start(blueprint_env)
    await event(blueprint_env, "btn_down")
    await event(blueprint_env, "single_push")
    await event(blueprint_env, "double_push")
    assert [call.entity_ids for call in blueprint_env.calls] == [{"light.hall_spot_1", "light.hall_spot_2"}, {"light.hall_ceiling", "light.hall_strip"}]


@pytest.mark.parametrize("kind", ["single_push", "double_push", "triple_push"])
async def test_a_press_without_a_preceding_event_is_lost(blueprint_env, kind):
    # After a restart the attribute is missing (None). A press right away is a change from None, which no `from`
    # list contains, so it is lost. A real press starts with btn_down, so this only matters for a device that does not.
    await start(blueprint_env)
    await event(blueprint_env, kind)
    assert names(blueprint_env) == []
