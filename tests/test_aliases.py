"""YAML aliases (`&anchor` / `*name`) in the files that tests load: they work, the shared parts are independent, and what an
alias may expand to is limited, in the test environment as in the mutation tool (they use the same code)."""

import time

import pytest

from ha_blueprint_test_harness import BlueprintLoadError, _yaml, env as harness_env

BOMB = "l0: &a0 [x, x]\n" + "".join(f"l{i}: &a{i} [*a{i - 1}, *a{i - 1}]\n" for i in range(1, 30))

AUTOMATION = """
id: alias_probe
triggers:
  - trigger: state
    entity_id: binary_sensor.door
    to: "on"
actions:
  - action: light.turn_on
    target: &hall
      entity_id: [light.hall_1, light.hall_2]
    data: &bright
      brightness: 100
  - action: light.turn_off
    target: *hall
  - action: light.turn_on
    target: *hall
    data: *bright
  - variables:
      lights: &list [light.a, light.b]
  - repeat:
      for_each: *list
      sequence:
        - action: light.toggle
          target:
            entity_id: "{{ repeat.item }}"
"""

BLUEPRINT = """
blueprint:
  name: Alias probe
  domain: automation
  input:
    light:
      name: Light
      selector:
        entity: {}
triggers:
  - trigger: state
    entity_id: binary_sensor.door
    to: "on"
actions:
  - action: light.turn_on
    target: &t
      entity_id: !input light
  - action: light.turn_off
    target: *t
"""


async def test_an_automation_file_with_aliases_runs(blueprint_env, tmp_path):
    path = tmp_path / "a.yaml"
    path.write_text(AUTOMATION, encoding="utf-8")
    await blueprint_env.start_automation(path, states={"binary_sensor.door": "off"}, services=["light.turn_on", "light.turn_off", "light.toggle"])
    await blueprint_env.set_state("binary_sensor.door", "on")
    assert [(c.name, sorted(c.entity_ids)) for c in blueprint_env.calls] == [
        ("light.turn_on", ["light.hall_1", "light.hall_2"]),
        ("light.turn_off", ["light.hall_1", "light.hall_2"]),
        ("light.turn_on", ["light.hall_1", "light.hall_2"]),
        ("light.toggle", ["light.a"]),
        ("light.toggle", ["light.b"]),
    ]
    assert blueprint_env.calls[2].data["brightness"] == 100


async def test_a_blueprint_with_aliases_and_input_runs(blueprint_env, tmp_path):
    # An anchor that holds an !input, used twice: the shape of a real blueprint.
    path = tmp_path / "b.yaml"
    path.write_text(BLUEPRINT, encoding="utf-8")
    await blueprint_env.start(path, {"light": "light.x"}, states={"binary_sensor.door": "off"}, services=["light.turn_on", "light.turn_off"])
    await blueprint_env.set_state("binary_sensor.door", "on")
    assert [(c.name, sorted(c.entity_ids)) for c in blueprint_env.calls] == [("light.turn_on", ["light.x"]), ("light.turn_off", ["light.x"])]


def test_the_shared_parts_of_an_automation_file_are_independent(tmp_path):
    path = tmp_path / "a.yaml"
    path.write_text(AUTOMATION, encoding="utf-8")
    config = harness_env._load_automation(path, None)
    first, second, third = config["actions"][0]["target"], config["actions"][1]["target"], config["actions"][2]["target"]
    assert first == second == third and first is not second and second is not third
    second["entity_id"].append("light.changed")
    assert first["entity_id"] == ["light.hall_1", "light.hall_2"]


async def test_an_alias_bomb_as_a_blueprint_is_refused_at_once(blueprint_env, tmp_path):
    path = tmp_path / "bomb.yaml"
    path.write_text("blueprint:\n  name: Bomb\n  domain: automation\n" + BOMB + "triggers: []\nactions: []\n", encoding="utf-8")
    started = time.monotonic()
    with pytest.raises(BlueprintLoadError, match="expands to more than"):
        await blueprint_env.start(path, {}, services=["light.turn_on"])
    assert time.monotonic() - started < 3


async def test_an_alias_bomb_as_an_automation_file_is_refused_at_once(blueprint_env, tmp_path):
    path = tmp_path / "bomb.yaml"
    path.write_text(BOMB + "triggers: []\nactions: []\n", encoding="utf-8")
    started = time.monotonic()
    with pytest.raises(ValueError, match="expands to more than"):
        await blueprint_env.start_automation(path, services=["light.turn_on"])
    assert time.monotonic() - started < 3


def test_the_check_reads_files_with_tags_and_invalid_yaml_without_failing():
    # The check only measures aliases; tags such as !input and invalid text are not its business.
    assert _yaml.check_expansion("a: !input x\nb: &y [1]\nc: *y\n") is None
    assert _yaml.check_expansion("a: [unclosed\n") is None


def test_a_file_with_many_ordinary_aliases_is_accepted():
    text = "base: &b {a: 1, b: [1, 2, 3]}\n" + "".join(f"k{i}: *b\n" for i in range(500))
    assert _yaml.check_expansion(text) is None


def test_the_limit_is_on_the_expanded_size():
    assert _yaml.expanded_size({"a": [1, 2, 3]}, 100) == 6      # the dict, the key, the list and its three values
    shared = [1] * 10
    assert _yaml.expanded_size({"x": shared, "y": shared}, 1000) == 1 + 2 + 2 * 11
    assert _yaml.expanded_size([[0] * 100 for _ in range(100)], 500) > 500
