"""The mutation tool itself: what it finds, how it judges, and that a broken blueprint is reported as such."""

import pathlib

import homeassistant.components.automation as automation
import pytest

from ha_blueprint_test_harness import BlueprintLoadError
from ha_blueprint_test_harness import mutate

MOTION_LIGHT = pathlib.Path(automation.__file__).parent / "blueprints" / "motion_light.yaml"


def test_round_trip_keeps_tags_and_values():
    # Reading and writing a blueprint must not change it, in particular not the !input tags.
    document = mutate.load(MOTION_LIGHT.read_text())
    again = mutate.load(mutate.dump(document))
    assert again == document
    assert any(f"!input {quote}motion_entity{quote}" in mutate.dump(document) for quote in ("", "'"))


def test_motion_light_yields_the_expected_kinds_of_mutants():
    # motion_light.yaml should yield each kind of change that applies to it, and no others.
    found = {m.operator for m in mutate.find_mutants(mutate.load(MOTION_LIGHT.read_text()))}
    assert found == {"mode", "drop_key", "swap_from_to", "number", "action_swap", "drop_item"}


def test_every_mutant_differs_from_the_original_and_ids_are_unique():
    # Every mutant really changes the YAML and has its own ID.
    document = mutate.load(MOTION_LIGHT.read_text())
    original = mutate.dump(document)
    mutants = mutate.find_mutants(document)
    assert len({m.id for m in mutants}) == len(mutants) > 10
    assert all(m.build(document) != original for m in mutants)


def test_building_a_mutant_does_not_change_the_parsed_document():
    # Building mutants works on copies; the parsed blueprint stays as it was.
    document = mutate.load(MOTION_LIGHT.read_text())
    before = mutate.dump(document)
    for mutant in mutate.find_mutants(document):
        mutant.build(document)
    assert mutate.dump(document) == before


def test_each_comparison_in_a_chain_is_mutated_on_its_own():
    # In '0 <= a <= b' each comparison is changed separately, giving two mutants.
    document = {"actions": [{"condition": "template", "value_template": "{{ 0 <= a <= b }}"}]}
    texts = sorted(m.build(document) for m in mutate.find_mutants(document) if m.operator == "template")
    assert [t for t in texts if "0 < a <= b" in t] and [t for t in texts if "0 <= a < b" in t]
    assert len(texts) == 2


@pytest.mark.parametrize("text", ["{{ a<b }}", "{{ '<b>bold</b>' }}", "{{ x }}", "plain text with < and and"])
def test_no_template_mutants_where_the_operator_is_not_a_spaced_comparison(text):
    # HTML like '<b>', 'a<b' without spaces and plain text are not mistaken for comparisons.
    document = {"actions": [{"data": {"message": text}}]}
    assert [m for m in mutate.find_mutants(document) if m.operator == "template"] == []


def test_boolean_words_and_not_in_templates():
    # 'and' becomes 'or' and 'not' is removed inside templates.
    document = {"actions": [{"condition": "template", "value_template": "{{ not a and b }}"}]}
    descriptions = {m.description for m in mutate.find_mutants(document) if m.operator == "template"}
    assert any("'and' -> 'or'" in d for d in descriptions) and any("remove 'not'" in d for d in descriptions)


def test_header_is_left_alone_except_input_defaults():
    # In the blueprint header only input defaults are changed; names and descriptions stay.
    document = {"blueprint": {"name": "x {{ not a }}", "input": {"wait": {"default": 120}, "flag": {"default": True}}},
                "mode": "restart"}
    found = {(m.operator, m.description.split(":")[0]) for m in mutate.find_mutants(document)}
    assert found == {("number", "blueprint.input.wait.default"), ("bool", "blueprint.input.flag.default"),
                     ("mode", "mode")}


def test_a_single_trigger_is_not_dropped_but_one_of_two_is():
    # A lone trigger is kept (no trigger would fail for a boring reason); with two, each can be dropped.
    one = {"triggers": [{"trigger": "state", "entity_id": "a.b"}]}
    two = {"triggers": [{"trigger": "state", "entity_id": "a.b"}, {"trigger": "state", "entity_id": "c.d"}]}
    assert not [m for m in mutate.find_mutants(one) if m.operator == "drop_item"]
    assert len([m for m in mutate.find_mutants(two) if m.operator == "drop_item"]) == 2


@pytest.mark.parametrize("code,output,timed_out,expected", [
    (0, "1 passed", False, "survived"),
    (1, "1 failed", False, "killed"),
    (1, "E   ha_blueprint_test_harness.env.BlueprintLoadError: x", False, "invalid"),
    (-1, "", True, "killed"),
    (2, "interrupted", False, "error"),
    (5, "no tests ran", False, "error"),
])
def test_classify(code, output, timed_out, expected):
    # Exit codes and output map to the right verdict: killed, survived, invalid or error.
    assert mutate.classify(code, output, timed_out) == expected


def test_score_counts_only_loadable_mutants():
    # The score is killed / (killed + survived); 'invalid' and 'error' are not counted.
    m = mutate.Mutant("M1", "x", "d", lambda _: None)
    report = mutate.Report([mutate.Result(m, "killed"), mutate.Result(m, "killed"), mutate.Result(m, "survived"),
                            mutate.Result(m, "invalid"), mutate.Result(m, "error")])
    assert report.score == pytest.approx(2 / 3)
    assert mutate.Report([mutate.Result(m, "invalid")]).score is None


async def test_a_blueprint_that_does_not_load_is_reported_as_such(blueprint_env, tmp_path):
    # A blueprint without its trigger entity does not load; start() must say so (BlueprintLoadError).
    broken = tmp_path / "broken.yaml"
    broken.write_text(MOTION_LIGHT.read_text().replace("  entity_id: !input motion_entity\n  from:", "  from:", 1))
    with pytest.raises(BlueprintLoadError):
        await blueprint_env.start(broken, {"motion_entity": "binary_sensor.m", "light_target": {"entity_id": "light.l"}})


@pytest.mark.parametrize("argv,own,command", [
    (["bp.yaml", "--", "pytest", "-q"], ["bp.yaml"], ["pytest", "-q"]),
    (["bp.yaml", "--timeout", "90", "--", "pytest", "--timeout", "5"], ["bp.yaml", "--timeout", "90"], ["pytest", "--timeout", "5"]),
    (["--timeout", "90", "bp.yaml"], ["--timeout", "90", "bp.yaml"], []),
])
def test_options_before_the_double_dash_are_ours_and_everything_after_it_is_the_test_command(argv, own, command):
    # Everything after '--' goes to the test command, even options with the same name as ours.
    assert mutate.split_command(argv) == (own, command)


def test_an_unstartable_test_command_is_a_clear_error(tmp_path):
    # A test command that cannot be started stops the run with a clear message, not a traceback.
    with pytest.raises(SystemExit, match="Cannot run the test command"):
        mutate.run_mutation(MOTION_LIGHT, ["/nonexistent/python", "-m", "pytest"], workdir=tmp_path)
