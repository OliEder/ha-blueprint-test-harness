"""start_automation(): an automation written directly (no blueprint header) runs in the harness."""

import pathlib

import pytest
import yaml

from ha_blueprint_test_harness import BlueprintLoadError

LAMP_ON = {
    "triggers": [{"trigger": "state", "entity_id": "binary_sensor.door", "to": "on"}],
    "actions": [{"action": "light.turn_on", "target": {"entity_id": "light.hall"}}],
}
LAMP_OFF = {
    "id": "lamp_off",
    "alias": "Lamp off",
    "triggers": [{"trigger": "state", "entity_id": "binary_sensor.door", "to": "off"}],
    "actions": [{"action": "light.turn_off", "target": {"entity_id": "light.hall"}}],
}
STATES = {"binary_sensor.door": "off", "light.hall": "off"}


async def test_an_automation_from_a_dict_runs(blueprint_env):
    # Arrange: the automation as a plain dict. Act: the door opens. Assert: the lamp was switched on.
    await blueprint_env.start_automation(LAMP_ON, states=STATES, services=["light.turn_on"])
    await blueprint_env.set_state("binary_sensor.door", "on")
    assert len(blueprint_env.calls_to("light.turn_on")) == 1


async def test_an_automation_from_a_file_runs(blueprint_env, tmp_path):
    # The same automation, read from a YAML file that holds one automation.
    path = tmp_path / "lamp.yaml"
    path.write_text(yaml.safe_dump(LAMP_ON), encoding="utf-8")
    await blueprint_env.start_automation(path, states=STATES, services=["light.turn_on"])
    await blueprint_env.set_state("binary_sensor.door", "on")
    assert len(blueprint_env.calls_to("light.turn_on")) == 1


@pytest.mark.parametrize("pick", ["lamp_off", "Lamp off"])
async def test_one_entry_of_a_list_is_picked_by_id_or_alias(blueprint_env, tmp_path, pick):
    # automations.yaml holds a list; `pick` chooses one entry, the others are ignored.
    path = tmp_path / "automations.yaml"
    path.write_text(yaml.safe_dump([{**LAMP_ON, "id": "lamp_on"}, LAMP_OFF]), encoding="utf-8")
    await blueprint_env.start_automation(path, pick=pick, states={**STATES, "binary_sensor.door": "on"}, services=["light.turn_on", "light.turn_off"])
    await blueprint_env.set_state("binary_sensor.door", "off")
    assert len(blueprint_env.calls_to("light.turn_off")) == 1
    assert blueprint_env.calls_to("light.turn_on") == []


async def test_a_list_without_pick_is_an_error(blueprint_env, tmp_path):
    # Two automations and no way to tell which one is meant: say so instead of guessing.
    path = tmp_path / "automations.yaml"
    path.write_text(yaml.safe_dump([LAMP_ON, LAMP_OFF]), encoding="utf-8")
    with pytest.raises(ValueError, match="pick"):
        await blueprint_env.start_automation(path)


async def test_a_pick_that_matches_nothing_is_an_error(blueprint_env, tmp_path):
    # A typo in `pick` must not silently load another automation.
    path = tmp_path / "automations.yaml"
    path.write_text(yaml.safe_dump([LAMP_OFF]), encoding="utf-8")
    with pytest.raises(ValueError, match="nothing"):
        await blueprint_env.start_automation(path, pick="no such automation")


async def test_a_broken_automation_is_reported(blueprint_env):
    # Home Assistant only logs an invalid automation; the harness turns that into an error.
    with pytest.raises(BlueprintLoadError):
        await blueprint_env.start_automation({"triggers": [{"trigger": "no_such_trigger"}], "actions": []})


async def test_the_trace_works_for_a_direct_automation(blueprint_env):
    # last_trace() finds the run of a directly loaded automation too.
    await blueprint_env.start_automation(LAMP_ON, states=STATES, services=["light.turn_on"])
    await blueprint_env.set_state("binary_sensor.door", "on")
    assert "action/0" in blueprint_env.last_trace().path


FORECAST = {
    "triggers": [{"trigger": "state", "entity_id": "binary_sensor.door", "to": "on"}],
    "actions": [
        {"action": "weather.get_forecasts", "data": {"type": "daily"}, "target": {"entity_id": "weather.home"}, "response_variable": "fc"},
        {"action": "light.turn_on", "target": {"entity_id": "light.hall"}, "data": {"brightness": "{{ fc['weather.home']['forecast'][0]['temperature'] | int }}"}},
    ],
}


async def test_a_service_with_a_response_feeds_the_next_step(blueprint_env):
    # `responses` registers the service so that response_variable works; the next action uses the answer.
    answer = {"weather.home": {"forecast": [{"temperature": 7}]}}
    await blueprint_env.start_automation(FORECAST, states=STATES, services=["light.turn_on"], responses={"weather.get_forecasts": answer})
    await blueprint_env.set_state("binary_sensor.door", "on")
    assert blueprint_env.calls_to("light.turn_on")[0].data["brightness"] == 7
    assert blueprint_env.calls_to("weather.get_forecasts")[0].data["type"] == "daily"


async def test_a_response_can_depend_on_the_call(blueprint_env):
    # A function gets the service call and returns the answer, so one service can answer differently per request.
    def answer(call):
        return {"weather.home": {"forecast": [{"temperature": 3 if call.data["type"] == "daily" else 9}]}}

    await blueprint_env.start_automation(FORECAST, states=STATES, services=["light.turn_on"], responses={"weather.get_forecasts": answer})
    await blueprint_env.set_state("binary_sensor.door", "on")
    assert blueprint_env.calls_to("light.turn_on")[0].data["brightness"] == 3


async def test_start_takes_responses_too(blueprint_env):
    # The same option exists for blueprints; here only the registration is checked.
    example = pathlib.Path(__file__).parents[1] / "docs" / "examples" / "window_heater.yaml"
    inputs = {"room_temperature": "sensor.room", "window": "binary_sensor.window", "heater": "switch.heater"}
    await blueprint_env.start(example, inputs, states={"sensor.room": "15", "binary_sensor.window": "off", "switch.heater": "off"},
                              services=["switch.turn_on"], responses={"weather.get_forecasts": {}})
    assert "get_forecasts" in blueprint_env.hass.services.async_services()["weather"]


async def test_a_service_that_is_both_plain_and_with_a_response_is_an_error(blueprint_env):
    # Asking for both is a mistake in the test; say so instead of picking one.
    with pytest.raises(ValueError, match="weather.get_forecasts"):
        await blueprint_env.start_automation(FORECAST, services=["weather.get_forecasts"], responses={"weather.get_forecasts": {}})


async def test_the_state_of_another_automation_can_be_set(blueprint_env):
    # Automations often read the state or `last_triggered` of other automations. Such a state is part of the scenario
    # and must not be mistaken for a second automation under test.
    states = {**STATES, "automation.other": ("on", {"current": 0})}
    await blueprint_env.start_automation(LAMP_ON, states=states, services=["light.turn_on"])
    await blueprint_env.set_state("binary_sensor.door", "on")
    assert len(blueprint_env.calls_to("light.turn_on")) == 1
