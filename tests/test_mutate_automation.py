"""The mutation tool on an automation written directly: it finds the same kinds of changes, picks one entry of a list,
and the harness swaps the mutant in when a test starts the automation from that file."""

import pathlib
import sys
import textwrap

import pytest
import yaml

from ha_blueprint_test_harness import mutate

ROOT = pathlib.Path(__file__).parents[1]
LAMP = {
    "id": "lamp",
    "alias": "Lamp",
    "triggers": [{"trigger": "state", "entity_id": "binary_sensor.door", "to": "on"}],
    "conditions": [{"condition": "template", "value_template": "{{ states('sensor.lux') | float(0) < 20 }}"}],
    "actions": [{"action": "light.turn_on", "target": {"entity_id": "light.hall"}}],
    "mode": "single",
}
OTHER = {"id": "other", "alias": "Other", "triggers": [{"trigger": "state", "entity_id": "binary_sensor.window", "to": "on"}], "actions": [{"action": "light.turn_off"}]}


def test_an_automation_yields_the_usual_kinds_of_mutants():
    # Plural keys (triggers, conditions, actions), a template condition, a service with an opposite and a mode.
    found = {m.operator for m in mutate.find_mutants(LAMP)}
    assert {"drop_key", "template", "action_swap", "mode", "drop_item"} <= found


def test_a_list_needs_pick_and_only_the_picked_entry_is_mutated():
    # automations.yaml holds a list: without pick the tool cannot know which entry is meant.
    document = [LAMP, OTHER]
    with pytest.raises(SystemExit, match="pick"):
        mutate.select_automation(document, None)
    entry, index = mutate.select_automation(document, "Other")
    assert index == 1 and entry == OTHER
    assert all("light.hall" not in m.description for m in mutate.find_mutants(entry))


def test_a_pick_that_matches_nothing_is_an_error():
    with pytest.raises(SystemExit, match="matches"):
        mutate.select_automation([LAMP, OTHER], "no such automation")


def test_the_mutant_is_written_back_into_the_whole_list():
    # The test run reads the same file shape as before, so `pick` still works inside the test.
    document = [LAMP, OTHER]
    entry, index = mutate.select_automation(document, "lamp")
    mutant = mutate.find_mutants(entry)[0]
    written = yaml.safe_load(mutate.dump(mutate.embed(document, index, mutant.mutated(entry))))
    assert len(written) == 2 and written[1] == OTHER and written[0] != LAMP


def test_a_single_entry_list_needs_no_pick():
    entry, index = mutate.select_automation([LAMP], None)
    assert entry == LAMP and index == 0


# A tiny project: one automation file and the tests for it, run by the mutation tool in a child process.
def _project(folder: pathlib.Path, assertions: str) -> pathlib.Path:
    (folder / "lamp.yaml").write_text(yaml.safe_dump({k: v for k, v in LAMP.items() if k != "conditions"}), encoding="utf-8")
    (folder / "conftest.py").write_text(textwrap.dedent('''\
        import pytest
        pytest_plugins = ["ha_blueprint_test_harness.pytest_plugin"]

        @pytest.fixture
        def expected_lingering_timers():
            return True
        '''), encoding="utf-8")
    (folder / "pytest.ini").write_text(f"[pytest]\nasyncio_mode = auto\nasyncio_default_fixture_loop_scope = function\naddopts = -p no:respx\npythonpath = {ROOT}\n", encoding="utf-8")
    (folder / "test_lamp.py").write_text(textwrap.dedent('''\
        import pathlib

        FILE = pathlib.Path(__file__).parent / "lamp.yaml"
        STATES = {"binary_sensor.door": "off", "light.hall": "off"}

        async def test_door_opens(blueprint_env):
            await blueprint_env.start_automation(FILE, states=STATES, services=["light.turn_on", "light.turn_off"])
            await blueprint_env.set_state("binary_sensor.door", "on")
        ''') + assertions, encoding="utf-8")
    return folder / "lamp.yaml"


def test_a_run_swaps_the_mutant_in_so_that_a_test_on_the_file_notices(tmp_path):
    # The test starts the automation from the file; the swapped service (turn_on -> turn_off) must make it fail.
    strong = tmp_path / "strong"
    strong.mkdir()
    automation = _project(strong, '    assert len(blueprint_env.calls_to("light.turn_on")) == 1\n')
    command = [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", str(strong)]
    report = mutate.run_mutation(automation, command, workdir=tmp_path / "work-strong", log=lambda _: None)
    killed = {r.mutant.operator for r in report.results if r.outcome == "killed"}
    assert "action_swap" in killed and report.count("error") == 0

