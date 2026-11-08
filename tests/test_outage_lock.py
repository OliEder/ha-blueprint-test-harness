"""Reference automation tests: outage_lock.yaml, a lock that is repeated until the device confirms it.

Covers triggers with `for:` and ids, `homeassistant: start`, `repeat` with `until` and `repeat.index`, `wait_template` with a
timeout, `continue_on_error`, an `or`/`and` condition on trigger ids, the `default` branch of `choose` and `mode: restart`.
A mocked service with an effect plays the wallbox that confirms (or does not confirm) the lock.
"""

import pathlib

from homeassistant.exceptions import HomeAssistantError

AUTOMATION = pathlib.Path(__file__).parent / "automations" / "outage_lock.yaml"
INVERTER, LOCK, MARKER, PROTECTION = "sensor.inverter_state", "select.wallbox_lock", "input_boolean.wallbox_locked_by_outage", "input_boolean.battery_protection"
SERVICES = ["select.select_option", "input_boolean.turn_on", "input_boolean.turn_off", "notify.phone"]


# A wallbox that takes the option it is given at once (the confirming case).
def obeys(hass, call):
    hass.states.async_set(LOCK, call.data["option"])


# A wallbox that ignores the first `ignored` requests and obeys the next one.
def obeys_after(ignored):
    seen = []

    def effect(hass, call):
        seen.append(call.data["option"])
        if len(seen) > ignored:
            hass.states.async_set(LOCK, call.data["option"])

    return effect


# Starts the automation with the given inverter state; `effect` plays the wallbox, none means it never confirms.
async def start(env, inverter="On Grid", marker="off", protection="off", effect=obeys):
    effects = {"select.select_option": effect} if effect else {}
    states = {INVERTER: inverter, LOCK: "0", MARKER: marker, PROTECTION: protection, "sensor.battery_level": "64"}
    await env.start_automation(AUTOMATION, states=states, services=SERVICES, effects=effects)


# The options asked of the wallbox so far, in order.
def asked(env):
    return [call.data["option"] for call in env.calls_to("select.select_option")]


# The titles of the notifications sent so far.
def titles(env):
    return [call.data["title"] for call in env.calls_to("notify.phone")]


# Lets the clock pass in steps of one timeout, so that each round of the repeat loop gets its turn.
async def pass_time(env, seconds, step=20):
    for _ in range(seconds // step):
        await env.advance(step)


async def test_an_outage_of_five_seconds_locks_the_wallbox_and_says_so(blueprint_env):
    await start(blueprint_env)
    await blueprint_env.set_state(INVERTER, "Off Grid")
    await blueprint_env.advance(5)
    assert asked(blueprint_env) == ["1"]
    assert [call.name for call in blueprint_env.calls if call.name.startswith("input_boolean")] == ["input_boolean.turn_on"]
    assert titles(blueprint_env) == ["Grid outage: wallbox locked"]
    assert "Wallbox locked." in blueprint_env.calls_to("notify.phone")[0].data["message"]
    assert "Battery 64 %" in blueprint_env.calls_to("notify.phone")[0].data["message"]


async def test_a_shorter_outage_does_nothing(blueprint_env):
    await start(blueprint_env)
    await blueprint_env.set_state(INVERTER, "Off Grid")
    await blueprint_env.advance(4)
    await blueprint_env.set_state(INVERTER, "On Grid")
    await blueprint_env.advance(60)
    assert blueprint_env.calls == []


async def test_the_lock_is_repeated_until_the_wallbox_confirms(blueprint_env):
    await start(blueprint_env, effect=obeys_after(2))
    await blueprint_env.set_state(INVERTER, "Off Grid")
    await blueprint_env.advance(5)
    await pass_time(blueprint_env, 60)
    assert asked(blueprint_env) == ["1", "1", "1"]
    assert "Wallbox locked." in blueprint_env.calls_to("notify.phone")[0].data["message"]


async def test_a_wallbox_that_never_confirms_is_asked_fifteen_times_and_reported(blueprint_env):
    await start(blueprint_env, effect=None)
    await blueprint_env.set_state(INVERTER, "Off Grid")
    await blueprint_env.advance(5)
    await pass_time(blueprint_env, 20 * 20)
    assert len(asked(blueprint_env)) == 15
    assert "NOT confirmed locked" in blueprint_env.calls_to("notify.phone")[0].data["message"]
    assert len(blueprint_env.calls_to("notify.phone")) == 1


async def test_the_grid_back_for_two_minutes_releases_the_wallbox(blueprint_env):
    await start(blueprint_env, inverter="Off Grid", marker="on")
    await blueprint_env.set_state(INVERTER, "On Grid")
    await blueprint_env.advance(119)
    assert asked(blueprint_env) == []
    await blueprint_env.advance(1)
    assert asked(blueprint_env) == ["0"]
    assert [call.name for call in blueprint_env.calls if call.name.startswith("input_boolean")] == ["input_boolean.turn_off"]
    assert titles(blueprint_env) == ["Grid is back: wallbox free"]


async def test_no_release_while_the_battery_protection_is_on(blueprint_env):
    await start(blueprint_env, inverter="Off Grid", marker="on", protection="on")
    await blueprint_env.set_state(INVERTER, "On Grid")
    await blueprint_env.advance(180)
    assert blueprint_env.calls == []


async def test_switching_the_protection_off_releases_a_locked_wallbox(blueprint_env):
    await start(blueprint_env, inverter="On Grid", marker="on", protection="on")
    await blueprint_env.set_state(PROTECTION, "off")
    assert asked(blueprint_env) == ["0"]


async def test_no_release_when_we_did_not_lock_it(blueprint_env):
    # The marker says the wallbox was not locked because of an outage: someone else's lock stays.
    await start(blueprint_env, inverter="On Grid", marker="off", protection="on")
    await blueprint_env.set_state(PROTECTION, "off")
    assert blueprint_env.calls == []


async def test_no_release_while_the_inverter_is_still_off_grid(blueprint_env):
    await start(blueprint_env, inverter="Off Grid", marker="on", protection="on")
    await blueprint_env.set_state(PROTECTION, "off")
    assert asked(blueprint_env) == []


# The `homeassistant: start` trigger waits once for the event `homeassistant_started`, which this test fires by hand
# (checked in Home Assistant 2026.10 and 2026.11; the trigger is armed when the automation is set up).
async def after_start(env, **kwargs):
    await start(env, **kwargs)
    await env.fire_event("homeassistant_started")


async def test_a_restart_during_an_outage_locks_again(blueprint_env):
    # Home Assistant starts while the inverter is off grid: the lock must be set again.
    await after_start(blueprint_env, inverter="Off Grid")
    assert asked(blueprint_env) == ["1"]


async def test_a_restart_with_the_grid_present_locks_nothing(blueprint_env):
    await after_start(blueprint_env, inverter="On Grid", marker="off")
    assert asked(blueprint_env) == []


async def test_a_restart_with_the_grid_back_releases_a_leftover_lock(blueprint_env):
    # The marker says the wallbox was locked before the restart, the grid is back and the protection is off.
    await after_start(blueprint_env, inverter="On Grid", marker="on", protection="off")
    assert asked(blueprint_env) == ["0"]


async def test_a_new_outage_during_the_repeat_starts_the_lock_again_from_the_beginning(blueprint_env):
    # mode restart: leaving and re-entering Off Grid while the loop runs throws the old loop away.
    await start(blueprint_env, effect=None)
    await blueprint_env.set_state(INVERTER, "Off Grid")
    await blueprint_env.advance(5)
    await pass_time(blueprint_env, 100)
    before = len(asked(blueprint_env))
    await blueprint_env.set_state(INVERTER, "On Grid")
    await blueprint_env.set_state(INVERTER, "Off Grid")
    await blueprint_env.advance(5)
    await blueprint_env.settle()
    assert len(asked(blueprint_env)) == before + 1


async def test_the_run_names_the_branch_it_took(blueprint_env):
    await start(blueprint_env)
    await blueprint_env.set_state(INVERTER, "Off Grid")
    await blueprint_env.advance(5)
    assert "action/0/choose/0/sequence/1" in blueprint_env.last_trace().path


async def test_every_command_names_its_target(blueprint_env):
    await start(blueprint_env)
    await blueprint_env.set_state(INVERTER, "Off Grid")
    await blueprint_env.advance(5)
    assert [call.entity_ids for call in blueprint_env.calls_to("select.select_option")] == [{LOCK}]
    assert [call.entity_ids for call in blueprint_env.calls_to("input_boolean.turn_on")] == [{MARKER}]


async def test_the_release_names_its_targets(blueprint_env):
    await start(blueprint_env, inverter="Off Grid", marker="on")
    await blueprint_env.set_state(INVERTER, "On Grid")
    await blueprint_env.advance(120)
    assert [call.entity_ids for call in blueprint_env.calls_to("select.select_option")] == [{LOCK}]
    assert [call.entity_ids for call in blueprint_env.calls_to("input_boolean.turn_off")] == [{MARKER}]


async def test_switching_the_protection_on_releases_nothing(blueprint_env):
    # Only the change to off counts.
    await start(blueprint_env, inverter="On Grid", marker="on", protection="off")
    await blueprint_env.set_state(PROTECTION, "on")
    assert blueprint_env.calls == []


async def test_a_failing_lock_command_is_tried_again(blueprint_env):
    # The wallbox answers the first request with an error; `continue_on_error` keeps the loop going.
    attempts = []

    def flaky(hass, call):
        attempts.append(call.data["option"])
        if len(attempts) == 1:
            raise HomeAssistantError("the wallbox did not answer")
        hass.states.async_set(LOCK, call.data["option"])

    await start(blueprint_env, effect=flaky)
    await blueprint_env.set_state(INVERTER, "Off Grid")
    await blueprint_env.advance(5)
    await pass_time(blueprint_env, 40)
    assert len(attempts) == 2
    assert "Wallbox locked." in blueprint_env.calls_to("notify.phone")[0].data["message"]


async def test_an_attribute_change_of_the_protection_switch_releases_nothing(blueprint_env):
    # The trigger is the change *to* off; the switch staying off with a new attribute is no trigger.
    await start(blueprint_env, inverter="On Grid", marker="on", protection="off")
    await blueprint_env.set_state(PROTECTION, "off", {"note": "changed"})
    assert blueprint_env.calls == []
