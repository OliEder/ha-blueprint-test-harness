"""Reference automation tests: humidity_warning.yaml, an automation written directly (no blueprint header).

Covers a numeric_state trigger with `for:` on several sensors, a lookup table keyed by `trigger.entity_id`, a formula
(absolute humidity from temperature and relative humidity), the guard against a sensor that comes back from
unavailable, and defaults for missing values.
"""

import math
import pathlib

AUTOMATION = pathlib.Path(__file__).parent / "automations" / "humidity_warning.yaml"
BATH, LAUNDRY = "sensor.bathroom_humidity", "sensor.laundry_humidity"
WEATHER, NOTIFY = "weather.home", "notify.phone"
HOUR = 3600


# The absolute humidity (g/m3) of air at temperature t (degrees) and relative humidity rh (percent), rounded to 0.1.
def absolute_humidity(t, rh):
    return round(216.7 * (rh / 100 * 6.112 * math.exp(17.62 * t / (243.12 + t))) / (273.15 + t), 1)


# Starts the automation with the bathroom at 60 % and a given outside weather (temperature, humidity) or none.
async def start(env, bath="60", ah_in="9.0", weather=("5", "80"), **extra):
    states = {
        BATH: bath, LAUNDRY: "50",
        "sensor.bathroom_absolute_humidity": ah_in, "sensor.bathroom_dew_point": "12.34", "sensor.bathroom_temperature": "21.04",
        WEATHER: ("sunny", {"temperature": float(weather[0]), "humidity": float(weather[1])}) if weather else "sunny",
    }
    states.update(extra)
    await env.start_automation(AUTOMATION, states=states, services=[NOTIFY])


# Sets the bathroom humidity and lets the given hours pass.
async def humid(env, hours=3, value="75"):
    await env.set_state(BATH, value)
    await env.advance(hours * HOUR)


# The data of the first notification.
def first(env):
    return env.calls_to(NOTIFY)[0].data


async def test_three_hours_above_70_warns_and_airing_helps(blueprint_env):
    await start(blueprint_env, ah_in="12.0")
    await humid(blueprint_env)
    assert len(blueprint_env.calls_to(NOTIFY)) == 1
    variables = blueprint_env.last_trace().variables
    assert variables["ah_out"] == absolute_humidity(5, 80) and variables["airing_helps"] is True
    assert first(blueprint_env)["title"] == "Mold risk: Bathroom"
    assert "Airing helps" in first(blueprint_env)["message"]
    assert "now 75 %, 21.0 °C, dew point 12.3 °C" in first(blueprint_env)["message"]


async def test_just_under_three_hours_does_not_warn(blueprint_env):
    await start(blueprint_env)
    await humid(blueprint_env, hours=3 - 1 / 60)
    assert blueprint_env.calls_to(NOTIFY) == []


async def test_dropping_below_70_cancels_the_wait(blueprint_env):
    await start(blueprint_env)
    await humid(blueprint_env, hours=2)
    await blueprint_env.set_state(BATH, "69")
    await blueprint_env.advance(2 * HOUR)
    assert blueprint_env.calls_to(NOTIFY) == []


async def test_exactly_70_is_not_above(blueprint_env):
    await start(blueprint_env)
    await humid(blueprint_env, value="70")
    assert blueprint_env.calls_to(NOTIFY) == []


async def test_humid_outside_air_says_airing_does_not_help(blueprint_env):
    await start(blueprint_env, ah_in="9.0", weather=("15", "95"))
    await humid(blueprint_env)
    assert blueprint_env.last_trace().variables["airing_helps"] is False
    assert "Airing does not help" in first(blueprint_env)["message"]


async def test_airing_needs_a_margin_of_one_gram(blueprint_env):
    await start(blueprint_env, ah_in=str(absolute_humidity(5, 80) + 1.0))
    await humid(blueprint_env)
    assert blueprint_env.last_trace().variables["airing_helps"] is False


async def test_airing_helps_just_over_the_margin(blueprint_env):
    await start(blueprint_env, ah_in=str(absolute_humidity(5, 80) + 1.1))
    await humid(blueprint_env)
    assert blueprint_env.last_trace().variables["airing_helps"] is True


async def test_each_room_names_itself(blueprint_env):
    await start(blueprint_env, **{"sensor.laundry_absolute_humidity": "9", "sensor.laundry_dew_point": "8", "sensor.laundry_temperature": "14"})
    await blueprint_env.set_state(LAUNDRY, "80")
    await blueprint_env.advance(3 * HOUR)
    assert first(blueprint_env)["title"] == "Mold risk: Laundry"


async def test_two_rooms_at_the_same_time_both_warn(blueprint_env):
    await start(blueprint_env, **{"sensor.laundry_absolute_humidity": "9", "sensor.laundry_dew_point": "8", "sensor.laundry_temperature": "14"})
    blueprint_env.hass.states.async_set(BATH, "75")
    blueprint_env.hass.states.async_set(LAUNDRY, "80")
    await blueprint_env.settle()
    await blueprint_env.advance(3 * HOUR)
    assert sorted(call.data["title"] for call in blueprint_env.calls_to(NOTIFY)) == ["Mold risk: Bathroom", "Mold risk: Laundry"]


async def test_a_sensor_coming_back_from_unavailable_does_not_warn(blueprint_env):
    await start(blueprint_env, bath="unavailable")
    await humid(blueprint_env)
    assert blueprint_env.calls_to(NOTIFY) == []


async def test_a_sensor_coming_back_from_unknown_does_not_warn(blueprint_env):
    await start(blueprint_env, bath="unknown")
    await humid(blueprint_env)
    assert blueprint_env.calls_to(NOTIFY) == []


async def test_missing_weather_falls_back_to_10_degrees_and_70_percent(blueprint_env):
    await start(blueprint_env, weather=None)
    await humid(blueprint_env)
    assert blueprint_env.last_trace().variables["ah_out"] == absolute_humidity(10, 70)


async def test_missing_inside_value_gives_a_misleading_message(blueprint_env):
    # Known weakness of the automation, kept as a test: without the room's absolute humidity it uses 0 g/m3 and says
    # that airing does not help, although it cannot know.
    await start(blueprint_env, ah_in="unavailable")
    await humid(blueprint_env)
    assert blueprint_env.last_trace().variables["ah_in"] == 0.0
    assert "Airing does not help" in first(blueprint_env)["message"]


async def test_below_zero_outside(blueprint_env):
    await start(blueprint_env, ah_in="6.0", weather=("-5", "90"))
    await humid(blueprint_env)
    assert blueprint_env.last_trace().variables["ah_out"] == absolute_humidity(-5, 90)


async def test_inside_humidity_is_shown_with_one_decimal(blueprint_env):
    await start(blueprint_env, ah_in="12.34")
    await humid(blueprint_env)
    assert "inside 12.3 g/m³" in first(blueprint_env)["message"]


async def test_the_advice_when_airing_does_not_help_is_complete(blueprint_env):
    await start(blueprint_env, ah_in="9.0", weather=("15", "95"))
    await humid(blueprint_env)
    assert "Better heat the room slightly or dehumidify." in first(blueprint_env)["message"]
