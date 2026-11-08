"""start_automation(): an automation written directly (no blueprint header) runs in the harness."""

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
