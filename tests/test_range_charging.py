"""Reference automation tests: range_charging.yaml, a chain of variables that plans the charging for the next workday.

Covers `last_trace().variables` for every step of the calculation, winter and summer, missing vehicle data, the correction
by the energy charged since the last report, weekdays and the "connected for ten minutes" trigger, with `when=` and a time zone.
"""

import datetime as dt
import pathlib
import zoneinfo

import pytest

AUTOMATION = pathlib.Path(__file__).parent / "automations" / "range_charging.yaml"
CAR, SOC, RANGE = "binary_sensor.car_connected", "sensor.car_battery_level", "sensor.car_range"
POWER, AGE, SESSION, MODE = "sensor.wallbox_power", "sensor.car_report_age", "sensor.wallbox_session_energy", "select.wallbox_mode"
SERVICES = ["number.set_value", "select.select_option", "notify.phone"]
NOTIFY = "notify.phone"

BERLIN = zoneinfo.ZoneInfo("Europe/Berlin")


# Thirty seconds before the evening trigger at 21:00 local time on the given date.
def evening(year, month, day):
    return dt.datetime(year, month, day, 20, 59, 30, tzinfo=BERLIN)


SUNDAY_EVENING = evening(2026, 11, 8)


# Starts the automation at the given moment with a car state and lets the clock pass 21:00.


async def go(env, when=SUNDAY_EVENING, soc="50", rng="150", car="on", mode="4", age="unknown", power="0", session="0"):
    await env.hass.config.async_set_time_zone("Europe/Berlin")
    states = {CAR: car, SOC: soc, RANGE: rng, POWER: power, AGE: age, SESSION: session, MODE: mode}
    await env.start_automation(AUTOMATION, states=states, services=SERVICES, when=when)
    await env.advance(31)


# The values written to the number entities, by entity id.
def numbers(env):
    return {next(iter(call.entity_ids)): call.data["value"] for call in env.calls_to("number.set_value")}


async def test_normal_case_plans_the_missing_energy(blueprint_env):
    await go(blueprint_env)
    v = blueprint_env.last_trace().variables
    needed = 140 * 1.2                      # winter
    expected = round((needed - 150) * (0.5 * 58) / 150 * 1000 * 1.1 / 10) * 10
    assert v["energy_wh"] == expected == 3830
    assert numbers(blueprint_env)["number.wallbox_energy_target"] == 3830
    assert numbers(blueprint_env)["number.wallbox_departure_time"] == 390
    assert [c.data["option"] for c in blueprint_env.calls_to("select.select_option")] == ["5"]


async def test_summer_needs_less(blueprint_env):
    await go(blueprint_env, when=evening(2026, 6, 7))   # a Sunday in June
    v = blueprint_env.last_trace().variables
    assert v["is_winter"] is False and v["needed_km"] == 140
    assert v["energy_wh"] == 0   # 150 km is more than the 140 km needed in summer, so nothing is missing


async def test_no_vehicle_data_uses_the_fixed_amount(blueprint_env):
    await go(blueprint_env, soc="unavailable", rng="unavailable")
    v = blueprint_env.last_trace().variables
    assert v["data_ok"] is False and v["energy_wh"] == 20000
    assert "Vehicle data unavailable" in blueprint_env.calls_to(NOTIFY)[0].data["message"]


async def test_only_soc_missing_uses_the_fixed_amount(blueprint_env):
    await go(blueprint_env, soc="unavailable", rng="150")
    assert blueprint_env.last_trace().variables["energy_wh"] == 20000


async def test_enough_range_switches_next_trip_back_to_eco(blueprint_env):
    await go(blueprint_env, soc="90", rng="300", mode="5")
    assert blueprint_env.last_trace().variables["energy_wh"] == 0
    assert [c.data["option"] for c in blueprint_env.calls_to("select.select_option")] == ["4"]
    assert blueprint_env.calls_to(NOTIFY) == []


async def test_enough_range_leaves_other_modes_alone(blueprint_env):
    await go(blueprint_env, soc="90", rng="300", mode="3")
    assert blueprint_env.calls_to("select.select_option") == []


async def test_exactly_enough_range_is_enough(blueprint_env):
    await go(blueprint_env, soc="50", rng="168", mode="5")      # needed 168 km in winter
    assert blueprint_env.last_trace().variables["energy_wh"] == 0


async def test_charging_corrects_the_old_vehicle_report(blueprint_env):
    # 11 kW for 60 min would be 11 kWh, but only 5 kWh were counted: 5/1.1 kWh on a 58 kWh battery
    await go(blueprint_env, soc="50", rng="150", age="60", power="11000", session="5")
    v = blueprint_env.last_trace().variables
    assert v["charged_kwh"] == pytest.approx(5 / 1.1)
    assert v["soc"] == pytest.approx(50 + 5 / 1.1 / 58 * 100)


async def test_the_corrected_state_never_exceeds_100_percent(blueprint_env):
    await go(blueprint_env, soc="99", rng="400", age="600", power="11000", session="50")
    assert blueprint_env.last_trace().variables["soc"] == 100


async def test_friday_evening_does_nothing(blueprint_env):
    await go(blueprint_env, when=evening(2026, 11, 6))
    assert blueprint_env.calls == []


async def test_not_plugged_in_does_nothing(blueprint_env):
    await go(blueprint_env, car="off")
    assert blueprint_env.calls == []


async def test_plugging_in_for_ten_minutes_triggers_on_a_workday(blueprint_env):
    await blueprint_env.hass.config.async_set_time_zone("Europe/Berlin")
    await blueprint_env.start_automation(AUTOMATION, states={CAR: "off", SOC: "50", RANGE: "150", POWER: "0", AGE: "unknown", SESSION: "0", MODE: "4"},
        services=SERVICES, when=dt.datetime(2026, 11, 9, 16, 0, tzinfo=dt.UTC))    # Monday afternoon
    await blueprint_env.set_state(CAR, "on")
    await blueprint_env.advance(540)
    assert blueprint_env.calls == []
    await blueprint_env.advance(61)
    assert numbers(blueprint_env)["number.wallbox_energy_target"] == 3830


@pytest.mark.parametrize("month,winter", [(3, True), (4, False), (10, False), (11, True), (12, True), (1, True), (2, True)])


async def test_winter_months(blueprint_env, month, winter):
    # The first Sunday of each month, in Berlin time: November to March counts as winter.
    day = next(d for d in range(1, 8) if dt.date(2026, month, d).weekday() == 6)
    await go(blueprint_env, when=evening(2026, month, day))
    assert blueprint_env.last_trace().variables["is_winter"] is winter


async def test_charging_below_1_kw_is_not_counted(blueprint_env):
    await go(blueprint_env, age="60", power="800", session="5")
    assert blueprint_env.last_trace().variables["charged_kwh"] == 0


async def test_charging_just_above_1_kw_is_counted(blueprint_env):
    await go(blueprint_env, age="60", power="1100", session="5")
    assert blueprint_env.last_trace().variables["charged_kwh"] > 0


async def test_message_mentions_the_report_age_even_when_zero(blueprint_env):
    await go(blueprint_env, age="0")
    assert "Vehicle data from 0 min ago." in blueprint_env.calls_to(NOTIFY)[0].data["message"]


async def test_message_has_no_age_when_unknown(blueprint_env):
    await go(blueprint_env, age="unknown")
    assert "Vehicle data from" not in blueprint_env.calls_to(NOTIFY)[0].data["message"]


async def test_both_commands_and_the_mode_go_to_the_wallbox(blueprint_env):
    await go(blueprint_env)
    assert {entity: value for entity, value in numbers(blueprint_env).items()} == {"number.wallbox_energy_target": 3830, "number.wallbox_departure_time": 390}
    assert [call.entity_ids for call in blueprint_env.calls_to("select.select_option")] == [{MODE}]


async def test_leaving_the_next_trip_mode_targets_the_wallbox(blueprint_env):
    await go(blueprint_env, soc="90", rng="300", mode="5")
    assert [call.entity_ids for call in blueprint_env.calls_to("select.select_option")] == [{MODE}]


async def test_a_plan_without_charging_does_not_claim_that_something_was_charged(blueprint_env):
    await go(blueprint_env, age="30")
    assert "Charged since then" not in blueprint_env.calls_to(NOTIFY)[0].data["message"]


async def test_exactly_one_kilowatt_is_not_counted_as_charging(blueprint_env):
    await go(blueprint_env, age="60", power="1000", session="5")
    assert blueprint_env.last_trace().variables["charged_kwh"] == 0


async def test_a_charge_level_of_zero_is_no_data(blueprint_env):
    # 0 % cannot be told from a missing value: the automation falls back to the fixed amount (and must not divide by it).
    await go(blueprint_env, soc="0", rng="100")
    variables = blueprint_env.last_trace().variables
    assert variables["data_ok"] is False and variables["energy_wh"] == 20000


async def test_a_range_of_zero_is_no_data(blueprint_env):
    await go(blueprint_env, soc="50", rng="0")
    variables = blueprint_env.last_trace().variables
    assert variables["data_ok"] is False and variables["energy_wh"] == 20000


async def test_a_missing_range_stays_missing_even_while_charging(blueprint_env):
    # The range is only scaled when both values exist; otherwise it keeps the "missing" marker -1.
    await go(blueprint_env, soc="50", rng="unavailable", age="60", power="11000", session="5")
    assert blueprint_env.last_trace().variables["range_km"] == -1


async def test_an_attribute_change_of_the_connected_sensor_does_not_start_a_run(blueprint_env):
    # Only the change *to* on (after ten minutes) counts, not any other change of a car that is already connected.
    await blueprint_env.hass.config.async_set_time_zone("Europe/Berlin")
    await blueprint_env.start_automation(AUTOMATION, states={CAR: "on", SOC: "50", RANGE: "150", POWER: "0", AGE: "unknown", SESSION: "0", MODE: "4"},
                                         services=SERVICES, when=dt.datetime(2026, 11, 9, 16, 0, tzinfo=dt.UTC))
    await blueprint_env.set_state(CAR, "on", {"note": "changed"})
    await blueprint_env.advance(11 * 60)
    assert blueprint_env.calls == []


async def test_nothing_is_added_to_a_charge_level_of_zero_while_charging(blueprint_env):
    # Without a usable charge level there is no base to correct, so the charged energy stays 0.
    await go(blueprint_env, soc="0", rng="100", age="60", power="11000", session="5")
    assert blueprint_env.last_trace().variables["charged_kwh"] == 0
