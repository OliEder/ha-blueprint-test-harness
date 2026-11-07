"""Second user of the harness: a small original blueprint that needs a time pattern, sun conditions and a choose block."""

import datetime as dt
import pathlib

import pytest

BLUEPRINT = pathlib.Path(__file__).parent / "blueprints" / "daylight_heartbeat.yaml"
SERVICE = "test_sink.report"
# Times in the default test zone (US/Pacific): 13:00 is day, 03:00 is before sunrise, 22:00 is after sunset.
DAY = dt.datetime(2026, 6, 21, 20, 0, 0, tzinfo=dt.UTC)
BEFORE_SUNRISE = dt.datetime(2026, 6, 21, 10, 0, 0, tzinfo=dt.UTC)
AFTER_SUNSET = dt.datetime(2026, 6, 22, 5, 0, 0, tzinfo=dt.UTC)
INPUTS = {"value_sensor": "sensor.reading", "enabled_switch": "input_boolean.enabled"}


# Loads the blueprint at the given time with a sensor value and a switch state; extra inputs are optional.
async def start(env, when=DAY, reading="1200", switch="on", **inputs):
    await env.start(BLUEPRINT, {**INPUTS, **inputs}, services=[SERVICE], components=["sun"], when=when,
                    states={"sensor.reading": reading, "input_boolean.enabled": switch})


# The data of every recorded report, in order.
def reports(env):
    return [dict(call.data) for call in env.calls_to(SERVICE)]


async def test_daylight_reports_the_sensor_value(blueprint_env):
    # By day, the first time-pattern tick reports the sensor value once.
    await start(blueprint_env)
    await blueprint_env.advance(5)
    assert reports(blueprint_env) == [{"mode": "day", "value": 1200}]


async def test_daylight_reports_every_five_seconds(blueprint_env):
    # Three ticks, three reports: the time pattern really fires every 5 seconds.
    await start(blueprint_env)
    for _ in range(3):
        await blueprint_env.advance(5)
    assert len(reports(blueprint_env)) == 3


async def test_multiplier_is_applied(blueprint_env):
    # A reading of 2.5 with a multiplier of 1000 is reported as 2500.
    await start(blueprint_env, reading="2.5", multiplier=1000)
    await blueprint_env.advance(5)
    assert reports(blueprint_env) == [{"mode": "day", "value": 2500}]


@pytest.mark.parametrize("reading,expected", [("0.4", 0), ("0.6", 1), ("-1200", -1200), ("0", 0)])
async def test_value_is_rounded_to_a_whole_number(blueprint_env, reading, expected):
    # Rounding and the sign: a negative value is reported as it is, and zero is a usable value.
    await start(blueprint_env, reading=reading)
    await blueprint_env.advance(5)
    assert reports(blueprint_env) == [{"mode": "day", "value": expected}]


@pytest.mark.parametrize("bad", ["unavailable", "unknown", "abc", ""])
async def test_unusable_reading_is_not_reported_by_day(blueprint_env, bad):
    # A sensor value that is not a number must not turn into a made-up report.
    await start(blueprint_env, reading=bad)
    await blueprint_env.advance(5)
    assert blueprint_env.calls == []


async def test_unusable_reading_by_day_does_not_fall_through_to_the_night_report(blueprint_env):
    # Over a full minute (which includes the half-minute windows) nothing is sent by day when the reading is bad.
    await start(blueprint_env, reading="unavailable")
    for _ in range(12):
        await blueprint_env.advance(5)
    assert blueprint_env.calls == []


@pytest.mark.parametrize("multiplier", [0, -1])
async def test_unusable_multiplier_is_not_reported(blueprint_env, multiplier):
    # A multiplier of zero or below is rejected (boundary: zero).
    await start(blueprint_env, multiplier=multiplier)
    await blueprint_env.advance(5)
    assert blueprint_env.calls == []


@pytest.mark.parametrize("when", [DAY, BEFORE_SUNRISE])
async def test_nothing_is_reported_while_the_switch_is_off(blueprint_env, when):
    # The switch gates both branches, by day and by night.
    await start(blueprint_env, when=when, switch="off")
    for _ in range(12):
        await blueprint_env.advance(5)
    assert blueprint_env.calls == []


@pytest.mark.parametrize("when", [BEFORE_SUNRISE, AFTER_SUNSET])
async def test_night_reports_zero_twice_a_minute_at_most(blueprint_env, when):
    # Over one minute in 5-second steps, zeros go out at second 30 and second 0 and at no other tick.
    await start(blueprint_env, when=when)
    for _ in range(12):
        await blueprint_env.advance(5)
    assert reports(blueprint_env) == [{"mode": "night", "value": 0}] * 2


@pytest.mark.parametrize("when", [BEFORE_SUNRISE, AFTER_SUNSET])
async def test_night_report_comes_in_the_first_five_seconds_of_a_half_minute(blueprint_env, when):
    # No report at second 5 or 25, one at second 30, none again at second 35.
    await start(blueprint_env, when=when)
    await blueprint_env.advance(5)
    await blueprint_env.advance(20)
    assert blueprint_env.calls == []
    await blueprint_env.advance(5)
    assert len(blueprint_env.calls) == 1
    await blueprint_env.advance(5)
    assert len(blueprint_env.calls) == 1


async def test_night_zero_does_not_depend_on_the_sensor(blueprint_env):
    # Zero at night is sent even when the sensor is unavailable.
    await start(blueprint_env, when=BEFORE_SUNRISE, reading="unavailable")
    for _ in range(6):
        await blueprint_env.advance(5)
    assert reports(blueprint_env) == [{"mode": "night", "value": 0}]


async def test_no_daytime_value_after_sunset(blueprint_env):
    # After sunset the daytime branch must stay silent even with a good reading.
    await start(blueprint_env, when=AFTER_SUNSET)
    await blueprint_env.advance(5)
    assert blueprint_env.calls == []
