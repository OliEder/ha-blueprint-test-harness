"""Fixes from the security audit (2026-11-08): what a hostile blueprint file can do, and how the mutation tool treats
hostile input. Each test names the finding it covers."""

import os
import pathlib
import sys

import pytest

from ha_blueprint_test_harness import BlueprintLoadError, mutate

BLUEPRINT_HEAD = """blueprint:
  name: Test
  domain: automation
triggers:
  - trigger: state
    entity_id: binary_sensor.door
    to: "on"
actions:
  - action: notify.send
    data:
"""


# Writes a blueprint whose action data is the given YAML lines (already indented by six spaces).
def blueprint(folder: pathlib.Path, data_lines: str) -> pathlib.Path:
    path = folder / "bp.yaml"
    path.write_text(BLUEPRINT_HEAD + data_lines, encoding="utf-8")
    return path


# F1: Home Assistant reads a blueprint with its own YAML loader, which resolves these tags outside the template sandbox.
@pytest.mark.parametrize("tag,value", [
    ("!env_var", "AUDIT_SECRET"),
    ("!include", "/etc/hosts"),
    ("!include", "../secret.yaml"),
    ("!secret", "token"),
    ("!include_dir_list", "/tmp"),
    ("!include_dir_merge_named", "/tmp"),
    ("!bogus_tag", "x"),
])
async def test_a_blueprint_with_a_reading_tag_is_refused(blueprint_env, tmp_path, monkeypatch, tag, value):
    monkeypatch.setenv("AUDIT_SECRET", "must-not-appear")
    path = blueprint(tmp_path, f"      leak: {tag} {value}\n")
    with pytest.raises(BlueprintLoadError, match="YAML tag") as error:
        await blueprint_env.start(path, {}, states={"binary_sensor.door": "off"}, services=["notify.send"])
    assert tag in str(error.value) and "must-not-appear" not in str(error.value)
    assert blueprint_env.calls == []


async def test_the_refusal_also_covers_a_tag_deep_inside_and_a_verbatim_tag(blueprint_env, tmp_path):
    path = blueprint(tmp_path, "      deep:\n        - level: !<!env_var> AUDIT_SECRET\n")
    with pytest.raises(BlueprintLoadError, match="YAML tag"):
        await blueprint_env.start(path, {}, states={"binary_sensor.door": "off"}, services=["notify.send"])


async def test_input_is_still_allowed(blueprint_env, tmp_path):
    path = tmp_path / "bp.yaml"
    path.write_text(BLUEPRINT_HEAD.replace("blueprint:\n  name: Test", "blueprint:\n  name: Test\n  input:\n    who:\n      name: Who") + "      who: !input who\n", encoding="utf-8")
    await blueprint_env.start(path, {"who": "alice"}, states={"binary_sensor.door": "off"}, services=["notify.send"])
    await blueprint_env.set_state("binary_sensor.door", "on")
    assert blueprint_env.calls[0].data["who"] == "alice"


async def test_an_automation_file_cannot_read_files_either(blueprint_env, tmp_path, monkeypatch):
    # start_automation() reads plain YAML, which rejects these tags (checked in the audit); this keeps it that way.
    monkeypatch.setenv("AUDIT_SECRET", "must-not-appear")
    path = tmp_path / "automation.yaml"
    path.write_text("triggers: []\nactions:\n  - action: notify.send\n    data:\n      leak: !env_var AUDIT_SECRET\n", encoding="utf-8")
    with pytest.raises(Exception) as error:
        await blueprint_env.start_automation(path, services=["notify.send"])
    assert "must-not-appear" not in str(error.value)


# F2: aliases make the dumped YAML grow without limit; the mutation tool refuses them and very large input.
def test_yaml_aliases_are_refused_by_the_mutation_tool():
    text = "a: &x [1, 2]\nb: *x\n"
    with pytest.raises(ValueError, match="alias"):
        mutate.load(text)


def test_a_nest_of_aliases_is_refused_at_once_not_after_minutes():
    text = "l0: &a0 [x, x]\n" + "".join(f"l{i}: &a{i} [*a{i - 1}, *a{i - 1}]\n" for i in range(1, 12))
    with pytest.raises(ValueError, match="alias"):
        mutate.load(text)


def test_very_large_input_is_refused():
    with pytest.raises(ValueError, match="too large"):
        mutate.load("a: " + "x" * 2_000_000 + "\n")


def test_a_run_with_an_alias_stops_with_a_clear_message(tmp_path):
    path = tmp_path / "a.yaml"
    path.write_text("triggers: &t [{trigger: state, entity_id: a.b}]\nactions: []\nalso: *t\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="alias"):
        mutate.run_mutation(path, [sys.executable, "-c", "pass"], workdir=tmp_path / "work", log=lambda _: None)


# F3: --workdir must not write through a symlink or over an earlier run's files.
def test_a_symlink_in_the_workdir_is_not_followed(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    victim = tmp_path / "victim.txt"
    victim.write_text("keep me", encoding="utf-8")
    (work / "control.yaml").symlink_to(victim)
    path = tmp_path / "a.yaml"
    path.write_text("triggers: [{trigger: state, entity_id: a.b, to: 'on'}]\nactions: [{action: light.turn_on}]\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="workdir"):
        mutate.run_mutation(path, [sys.executable, "-c", "pass"], workdir=work, log=lambda _: None)
    assert victim.read_text(encoding="utf-8") == "keep me"


def test_files_of_an_earlier_run_in_the_workdir_stop_the_run(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    (work / "M001.yaml").write_text("old", encoding="utf-8")
    path = tmp_path / "a.yaml"
    path.write_text("triggers: [{trigger: state, entity_id: a.b, to: 'on'}]\nactions: [{action: light.turn_on}]\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="workdir"):
        mutate.run_mutation(path, [sys.executable, "-c", "pass"], workdir=work, log=lambda _: None)
    assert (work / "M001.yaml").read_text(encoding="utf-8") == "old"


def test_other_files_in_the_workdir_are_left_alone(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    (work / "notes.txt").write_text("mine", encoding="utf-8")
    path = tmp_path / "a.yaml"
    path.write_text("triggers: [{trigger: state, entity_id: a.b, to: 'on'}]\nactions: [{action: light.turn_on}]\n", encoding="utf-8")
    mutate.run_mutation(path, [sys.executable, "-c", "pass"], workdir=work, log=lambda _: None)
    assert (work / "notes.txt").read_text(encoding="utf-8") == "mine" and (work / "control.yaml").exists()


@pytest.mark.skipif(not hasattr(os, "O_NOFOLLOW"), reason="needs O_NOFOLLOW")
def test_writing_a_new_file_never_follows_a_link_or_overwrites(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("keep", encoding="utf-8")
    link = tmp_path / "link.yaml"
    link.symlink_to(target)
    with pytest.raises(OSError):
        mutate._write_new(link, "x")
    with pytest.raises(OSError):
        mutate._write_new(target, "x")
    assert target.read_text(encoding="utf-8") == "keep"
    fresh = tmp_path / "fresh.yaml"
    mutate._write_new(fresh, "ok")
    assert fresh.read_text(encoding="utf-8") == "ok"


# F8: only pytest's own failure line says that the blueprint did not load, not any text that a test prints.
def test_text_printed_by_a_test_cannot_fake_the_invalid_verdict():
    output = "----- Captured stdout call -----\nBlueprintLoadError\nE   AssertionError: BlueprintLoadError\n1 failed"
    assert mutate.classify(1, output, False) == "killed"


@pytest.mark.parametrize("output", [
    "E   ha_blueprint_test_harness.env.BlueprintLoadError: the automation did not come up",
    "E   BlueprintLoadError: x",
    "FAILED tests/test_x.py::test_y - ha_blueprint_test_harness.env.BlueprintLoadError: the automation did not come up",
])
def test_pytests_own_failure_lines_still_mean_invalid(output):
    assert mutate.classify(1, output, False) == "invalid"
