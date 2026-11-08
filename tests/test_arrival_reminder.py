"""Reference automation tests: arrival_reminder.yaml.

Covers a state trigger on two device trackers, a template condition on a helper, a delay, a service that returns an answer
(`calendar.get_events` through `responses=`), a loop with a namespace, `repeat` with `for_each` over notification
service names that are called by a template, `wait_template` with a timeout and a second `if` after it.
"""

import datetime as dt
import pathlib
import zoneinfo

AUTOMATION = pathlib.Path(__file__).parent / "automations" / "arrival_reminder.yaml"
ALICE, BOB = "device_tracker.alice_phone", "device_tracker.bob_phone"
PLUG, BATTERY, DRIVER, LEAD = "binary_sensor.car_plug", "sensor.car_battery_level", "input_text.driver", "input_number.departure_lead_hours"
NOW = dt.datetime(2026, 11, 10, 18, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin"))
SERVICES = ["notify.alice_phone", "notify.bob_phone"]


# The answer of calendar.get_events: one entry per match, each starting `hours` after NOW.
def calendar_with(*games):
    return {"calendar.home_games": {"events": [{"start": (NOW + dt.timedelta(hours=hours)).isoformat(), "end": (NOW + dt.timedelta(hours=hours + 2)).isoformat(), "summary": title} for hours, title in games]}}


# Starts the automation at NOW with both people away, the car unplugged and the given calendar, driver and battery.
async def start(env, games=((30, "Derby"),), driver="", battery="50", plug="off", lead="3.5", alice="not_home"):
    await env.hass.config.async_set_time_zone("Europe/Berlin")
    states = {ALICE: alice, BOB: "not_home", PLUG: plug, BATTERY: battery, DRIVER: driver, LEAD: lead}
    await env.start_automation(AUTOMATION, states=states, services=SERVICES, responses={"calendar.get_events": calendar_with(*games)}, when=NOW)


# Alice arrives and the ten minutes pass.
async def alice_arrives(env, minutes=10):
    await env.set_state(ALICE, "home")
    await env.advance(minutes * 60)


# The services that were called, in order (the notification services have the person in their name).
def called(env):
    return [call.name for call in env.calls if call.name.startswith("notify.")]


# The message of the first call to the given service.
def message(env, service):
    return env.calls_to(service)[0].data["message"]


async def test_an_arrival_with_a_match_ahead_reminds_both_when_nobody_is_recorded(blueprint_env):
    await start(blueprint_env, driver="")
    await alice_arrives(blueprint_env)
    assert called(blueprint_env) == ["notify.alice_phone", "notify.bob_phone"]


async def test_the_message_names_the_game_the_departure_and_the_battery(blueprint_env):
    # The match is 30 h ahead at 00:00 local time of the 12th; with 3.5 h lead the departure is at 20:30 on the 11th.
    await start(blueprint_env, games=((30, "Derby"),))
    await alice_arrives(blueprint_env)
    assert message(blueprint_env, "notify.alice_phone") == "The car is not plugged in. Departure for Derby at 20:30, battery 50 %."


async def test_only_the_recorded_driver_is_reminded(blueprint_env):
    await start(blueprint_env, driver="Alice")
    await alice_arrives(blueprint_env)
    assert called(blueprint_env) == ["notify.alice_phone"]


async def test_the_other_person_arriving_is_ignored_when_someone_else_drove(blueprint_env):
    await start(blueprint_env, driver="Bob")
    await alice_arrives(blueprint_env)
    assert called(blueprint_env) == []


async def test_plugging_in_within_ten_minutes_cancels_the_reminder(blueprint_env):
    await start(blueprint_env)
    await blueprint_env.set_state(ALICE, "home")
    await blueprint_env.advance(5 * 60)
    await blueprint_env.set_state(PLUG, "on")
    await blueprint_env.advance(6 * 60)
    assert called(blueprint_env) == []


async def test_the_reminder_waits_ten_minutes(blueprint_env):
    await start(blueprint_env)
    await blueprint_env.set_state(ALICE, "home")
    await blueprint_env.advance(9 * 60 + 59)
    assert called(blueprint_env) == []


async def test_no_match_in_the_calendar_means_no_reminder(blueprint_env):
    await start(blueprint_env, games=())
    await alice_arrives(blueprint_env)
    assert called(blueprint_env) == []


async def test_a_departure_more_than_36_hours_away_is_too_early(blueprint_env):
    # Match at 40.2 h, departure 3.5 h earlier: 36.7 h ahead.
    await start(blueprint_env, games=((40.2, "Derby"),))
    await alice_arrives(blueprint_env)
    assert called(blueprint_env) == []


async def test_a_departure_just_inside_36_hours_counts(blueprint_env):
    await start(blueprint_env, games=((39.4, "Derby"),))
    await alice_arrives(blueprint_env)
    assert called(blueprint_env)[:1] == ["notify.alice_phone"]


async def test_a_departure_in_the_past_is_skipped_and_the_next_game_is_used(blueprint_env):
    # The first match starts in 2 h: its departure (3.5 h earlier) is already over. The second, 30 h ahead, is the one named.
    await start(blueprint_env, games=((2, "Past game"), (30, "Derby")))
    await alice_arrives(blueprint_env)
    assert "Derby" in message(blueprint_env, "notify.alice_phone")


async def test_a_full_battery_needs_no_reminder(blueprint_env):
    await start(blueprint_env, battery="95")
    await alice_arrives(blueprint_env)
    assert called(blueprint_env) == []


async def test_a_battery_just_below_95_gets_a_reminder(blueprint_env):
    await start(blueprint_env, battery="94")
    await alice_arrives(blueprint_env)
    assert called(blueprint_env)[:1] == ["notify.alice_phone"]


async def test_an_unknown_battery_still_reminds_and_says_so(blueprint_env):
    await start(blueprint_env, battery="unavailable")
    await alice_arrives(blueprint_env)
    assert "battery unknown %" in message(blueprint_env, "notify.alice_phone")


async def test_a_second_reminder_follows_after_45_minutes_if_still_unplugged(blueprint_env):
    await start(blueprint_env)
    await alice_arrives(blueprint_env)
    first = len(called(blueprint_env))
    await blueprint_env.advance(44 * 60)
    assert len(called(blueprint_env)) == first
    await blueprint_env.advance(60)
    assert called(blueprint_env)[first:] == ["notify.alice_phone", "notify.bob_phone"]
    assert blueprint_env.calls_to("notify.alice_phone")[-1].data["title"] == "Car still not plugged in"


async def test_plugging_in_during_the_wait_ends_it_without_a_second_reminder(blueprint_env):
    await start(blueprint_env)
    await alice_arrives(blueprint_env)
    first = len(called(blueprint_env))
    await blueprint_env.set_state(PLUG, "on")
    await blueprint_env.advance(50 * 60)
    assert len(called(blueprint_env)) == first


async def test_a_custom_lead_time_moves_the_departure(blueprint_env):
    await start(blueprint_env, lead="1")
    await alice_arrives(blueprint_env)
    assert "at 23:00," in message(blueprint_env, "notify.alice_phone")


async def test_the_calendar_is_asked_for_48_hours_of_the_right_calendar(blueprint_env):
    await start(blueprint_env)
    await alice_arrives(blueprint_env)
    call = blueprint_env.calls_to("calendar.get_events")[0]
    assert call.entity_ids == {"calendar.home_games"} and call.data["duration"] == {"hours": 48}


async def test_a_change_that_is_not_an_arrival_starts_nothing(blueprint_env):
    # Alice is already home. Bob only moves from "not_home" to "work": no arrival, so no run.
    await start(blueprint_env, alice="home")
    await blueprint_env.set_state(BOB, "work")
    await blueprint_env.advance(11 * 60)
    assert called(blueprint_env) == []


async def test_bob_arriving_is_reminded_when_nobody_is_recorded(blueprint_env):
    await start(blueprint_env, driver="")
    await blueprint_env.set_state(BOB, "home")
    await blueprint_env.advance(10 * 60)
    assert called(blueprint_env) == ["notify.alice_phone", "notify.bob_phone"]


async def test_bob_arriving_is_ignored_when_alice_drove(blueprint_env):
    await start(blueprint_env, driver="Alice")
    await blueprint_env.set_state(BOB, "home")
    await blueprint_env.advance(10 * 60)
    assert called(blueprint_env) == []


async def test_a_second_arrival_during_the_wait_does_not_restart_it(blueprint_env):
    # mode single: the second trigger is dropped, the first run keeps its ten minutes.
    await start(blueprint_env)
    await blueprint_env.set_state(ALICE, "home")
    await blueprint_env.advance(5 * 60)
    await blueprint_env.set_state(BOB, "home")
    await blueprint_env.advance(5 * 60)
    assert called(blueprint_env)[:2] == ["notify.alice_phone", "notify.bob_phone"]


async def test_a_departure_exactly_now_is_not_ahead(blueprint_env):
    # The first game's departure is exactly the moment of the check (10 minutes after the arrival): it is skipped.
    await start(blueprint_env, games=((3.5 + 10 / 60, "Too late"), (30, "Derby")))
    await alice_arrives(blueprint_env)
    assert "Derby" in message(blueprint_env, "notify.alice_phone")


async def test_the_first_game_ahead_is_named_not_the_last(blueprint_env):
    await start(blueprint_env, games=((30, "First"), (45, "Second")))
    await alice_arrives(blueprint_env)
    assert "First" in message(blueprint_env, "notify.alice_phone") and "Second" not in message(blueprint_env, "notify.alice_phone")


async def test_a_departure_exactly_36_hours_ahead_counts(blueprint_env):
    await start(blueprint_env, games=((36 + 3.5 + 10 / 60, "Derby"),))
    await alice_arrives(blueprint_env)
    assert called(blueprint_env)[:1] == ["notify.alice_phone"]


async def test_an_empty_battery_is_shown_as_zero_not_as_unknown(blueprint_env):
    await start(blueprint_env, battery="0")
    await alice_arrives(blueprint_env)
    assert "battery 0 %" in message(blueprint_env, "notify.alice_phone")
