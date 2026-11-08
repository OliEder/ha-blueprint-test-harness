"""Documentation example: tests for frost_warning.yaml, an automation that uses the answer of a service.

Shows `responses=`: weather.get_forecasts returns data, so it cannot be a plain mocked service. The answer is a dict,
or a function of the call when it must depend on what was asked.
"""

import pathlib

AUTOMATION = pathlib.Path(__file__).parent / "frost_warning.yaml"


# The answer weather.get_forecasts gives: one entry per day, with the lowest temperature of that day.
def forecast(*lows):
    return {"weather.home": {"forecast": [{"templow": low} for low in lows]}}


# Starts the automation with a given answer and lets the evening begin.
async def evening(env, answer):
    await env.start_automation(AUTOMATION, states={"binary_sensor.evening": "off"}, services=["notify.phone"], responses={"weather.get_forecasts": answer})
    await env.set_state("binary_sensor.evening", "on")


async def test_a_frost_in_the_forecast_sends_the_lowest_value(blueprint_env):
    await evening(blueprint_env, forecast(3.0, -2.5, 8.0))
    assert [call.data["message"] for call in blueprint_env.calls_to("notify.phone")] == ["Frost tonight: -2.5 degrees"]


async def test_no_frost_sends_nothing(blueprint_env):
    await evening(blueprint_env, forecast(4.0, 2.0))
    assert blueprint_env.calls_to("notify.phone") == []


async def test_zero_degrees_is_not_frost(blueprint_env):
    await evening(blueprint_env, forecast(0.0, 1.0))
    assert blueprint_env.calls_to("notify.phone") == []


async def test_only_the_next_two_days_count(blueprint_env):
    await evening(blueprint_env, forecast(5.0, 5.0, -9.0))
    assert blueprint_env.calls_to("notify.phone") == []


async def test_the_forecast_is_asked_for_by_day(blueprint_env):
    # The call itself is recorded like any other service call.
    await evening(blueprint_env, forecast(1.0, 1.0))
    assert blueprint_env.calls_to("weather.get_forecasts")[0].data["type"] == "daily"


async def test_the_answer_can_depend_on_the_call(blueprint_env):
    # A function gets the service call and returns the answer.
    await evening(blueprint_env, lambda call: forecast(-1.0, 4.0) if call.data["type"] == "daily" else forecast(10.0))
    assert len(blueprint_env.calls_to("notify.phone")) == 1


async def test_the_forecast_is_asked_for_the_right_weather_entity(blueprint_env):
    # The target of the call is part of the behaviour: asking another entity would give another forecast.
    await evening(blueprint_env, forecast(1.0, 1.0))
    assert blueprint_env.calls_to("weather.get_forecasts")[0].entity_ids == {"weather.home"}


async def test_the_evening_ending_does_not_warn_again(blueprint_env):
    # Only the start of the evening (to: "on") triggers the run; switching it off must not.
    await evening(blueprint_env, forecast(-3.0, 0.0))
    await blueprint_env.set_state("binary_sensor.evening", "off")
    assert len(blueprint_env.calls_to("notify.phone")) == 1
