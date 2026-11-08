"""Documentation example: tests for car_driver.yaml, an automation written directly (no blueprint header).

Shows start_automation() with a file, waiting for a trigger with a timeout, a delay, `mode: restart` and the mutation
tool on an automation. Time moves in one-second steps wherever a loop or a restart is involved.
"""

import pathlib

AUTOMATION = pathlib.Path(__file__).parent / "car_driver.yaml"
PLUG, ALICE, BOB, FIELD = "binary_sensor.car_plug", "device_tracker.alice_phone", "device_tracker.bob_phone", "input_text.driver"


# Starts the automation with the car plugged in and both people at home (or as given).
async def start(env, alice="home", bob="home"):
    await env.start_automation(AUTOMATION, states={PLUG: "on", ALICE: alice, BOB: bob, FIELD: "old"}, services=["input_text.set_value"])


# The values written into the helper so far, in order.
def written(env):
    return [call.data["value"] for call in env.calls_to("input_text.set_value")]


# Unplugs the car, which starts the run.
async def unplug(env):
    await env.set_state(PLUG, "off")


async def test_the_person_who_leaves_is_remembered_after_three_minutes(blueprint_env):
    # Arrange: both at home. Act: unplug, Alice leaves. Assert: the helper is cleared first, then holds her name.
    await start(blueprint_env)
    await unplug(blueprint_env)
    assert written(blueprint_env) == [""]
    await blueprint_env.set_state(ALICE, "not_home")
    await blueprint_env.advance(180)
    assert written(blueprint_env) == ["", "Alice"]


async def test_both_leaving_are_listed_in_order(blueprint_env):
    await start(blueprint_env)
    await unplug(blueprint_env)
    await blueprint_env.set_state(ALICE, "not_home")
    await blueprint_env.set_state(BOB, "not_home")
    await blueprint_env.advance(180)
    assert written(blueprint_env)[-1] == "Alice,Bob"


async def test_someone_who_was_already_away_is_not_remembered(blueprint_env):
    await start(blueprint_env, bob="not_home")
    await unplug(blueprint_env)
    await blueprint_env.set_state(ALICE, "not_home")
    await blueprint_env.advance(180)
    assert written(blueprint_env)[-1] == "Alice"


async def test_nobody_leaving_within_twenty_minutes_leaves_the_helper_empty(blueprint_env):
    await start(blueprint_env)
    await unplug(blueprint_env)
    await blueprint_env.advance(20 * 60 + 1)
    await blueprint_env.advance(180)
    assert written(blueprint_env) == [""]


async def test_leaving_after_the_window_is_not_remembered(blueprint_env):
    await start(blueprint_env)
    await unplug(blueprint_env)
    await blueprint_env.advance(25 * 60)
    await blueprint_env.set_state(ALICE, "not_home")
    await blueprint_env.advance(180)
    assert written(blueprint_env) == [""]


async def test_leaving_just_inside_the_window_is_remembered(blueprint_env):
    await start(blueprint_env)
    await unplug(blueprint_env)
    await blueprint_env.advance(19 * 60)
    await blueprint_env.set_state(ALICE, "not_home")
    await blueprint_env.advance(180)
    assert written(blueprint_env)[-1] == "Alice"


async def test_coming_back_within_the_three_minutes_gives_an_empty_list(blueprint_env):
    await start(blueprint_env)
    await unplug(blueprint_env)
    await blueprint_env.set_state(ALICE, "not_home")
    await blueprint_env.advance(60)
    await blueprint_env.set_state(ALICE, "home")
    await blueprint_env.advance(130)
    assert written(blueprint_env)[-1] == ""


async def test_arriving_home_does_not_end_the_wait(blueprint_env):
    # Only a phone that leaves "home" counts. Bob was away and comes home: the helper stays as it was.
    await start(blueprint_env, bob="not_home")
    await unplug(blueprint_env)
    await blueprint_env.advance(300)
    await blueprint_env.set_state(BOB, "home")
    await blueprint_env.advance(600)
    assert written(blueprint_env) == [""]


async def test_unplugging_again_restarts_the_run(blueprint_env):
    # mode restart: the second unplug throws the first run away, so the 20 minutes start again.
    await start(blueprint_env)
    await unplug(blueprint_env)
    await blueprint_env.advance(600)
    await blueprint_env.set_state(PLUG, "on")
    await unplug(blueprint_env)
    await blueprint_env.advance(19 * 60)
    await blueprint_env.set_state(BOB, "not_home")
    await blueprint_env.advance(180)
    assert written(blueprint_env)[-1] == "Bob"


async def test_plugging_in_or_coming_back_from_unavailable_starts_nothing(blueprint_env):
    await start(blueprint_env)
    await blueprint_env.set_state(PLUG, "unavailable")
    await blueprint_env.set_state(PLUG, "off")
    await blueprint_env.set_state(PLUG, "on")
    assert written(blueprint_env) == []


async def test_both_writes_target_the_helper(blueprint_env):
    await start(blueprint_env)
    await unplug(blueprint_env)
    await blueprint_env.set_state(ALICE, "not_home")
    await blueprint_env.advance(180)
    assert [call.entity_ids for call in blueprint_env.calls_to("input_text.set_value")] == [{FIELD}, {FIELD}]


async def test_the_run_names_the_people_who_were_home(blueprint_env):
    # The trace shows the values the run worked with.
    await start(blueprint_env, bob="not_home")
    await unplug(blueprint_env)
    variables = blueprint_env.last_trace().variables
    assert variables["alice_was_home"] is True and variables["bob_was_home"] is False
