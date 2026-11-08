"""The mutation tool can run several mutants at the same time (`--jobs`). A fake test command stands in for pytest, so
these tests are fast and show the overlap directly."""

import pathlib
import sys
import textwrap
import time

import pytest
import yaml

from ha_blueprint_test_harness import mutate

LAMP = {
    "id": "lamp",
    "triggers": [{"trigger": "state", "entity_id": "binary_sensor.door", "to": "on", "for": "00:01:00"}],
    "conditions": [{"condition": "template", "value_template": "{{ states('sensor.lux') | float(0) < 20 }}"}],
    "actions": [{"action": "light.turn_on", "target": {"entity_id": "light.hall"}}],
    "mode": "single",
}

# The fake test command: it records when it starts and ends (one file per mutant), waits a little, and fails ("kills the
# mutant") when the mutant file contains `turn_off`. Without a mutant file (the first safety check) it succeeds.
FAKE = textwrap.dedent('''\
    import os, pathlib, sys, time
    mutant = os.environ.get("HA_BLUEPRINT_TEST_HARNESS_MUTANT")
    if mutant:
        stamp = pathlib.Path(sys.argv[1]) / pathlib.Path(mutant).stem
        stamp.with_suffix(".start").write_text(str(time.monotonic()))
        time.sleep(0.2)
        stamp.with_suffix(".end").write_text(str(time.monotonic()))
        sys.exit(1 if "turn_off" in pathlib.Path(mutant).read_text() else 0)
    ''')


# Writes the automation and the fake command; returns the automation path and the command to give to the tool.
def _setup(folder: pathlib.Path):
    automation = folder / "lamp.yaml"
    automation.write_text(yaml.safe_dump(LAMP), encoding="utf-8")
    script = folder / "fake_tests.py"
    script.write_text(FAKE, encoding="utf-8")
    stamps = folder / "stamps"
    stamps.mkdir()
    return automation, [sys.executable, str(script), str(stamps)], stamps


# True when two of the recorded runs were active at the same moment.
def _overlap(stamps: pathlib.Path) -> bool:
    spans = sorted((float(p.read_text()), float(p.with_suffix(".end").read_text())) for p in stamps.glob("*.start"))
    return any(later_start < earlier_end for (_, earlier_end), (later_start, _) in zip(spans, spans[1:]))


def test_runs_one_after_another_by_default(tmp_path):
    automation, command, stamps = _setup(tmp_path)
    mutate.run_mutation(automation, command, workdir=tmp_path / "work", log=lambda _: None)
    assert not _overlap(stamps)


def test_with_jobs_several_mutants_run_at_the_same_time(tmp_path):
    automation, command, stamps = _setup(tmp_path)
    mutate.run_mutation(automation, command, workdir=tmp_path / "work", jobs=4, log=lambda _: None)
    assert _overlap(stamps)


def test_the_result_is_the_same_and_in_the_same_order_as_without_jobs(tmp_path):
    automation, command, _ = _setup(tmp_path)
    one = mutate.run_mutation(automation, command, workdir=tmp_path / "one", log=lambda _: None)
    many = mutate.run_mutation(automation, command, workdir=tmp_path / "many", jobs=4, log=lambda _: None)
    assert [(r.mutant.id, r.outcome) for r in many.results] == [(r.mutant.id, r.outcome) for r in one.results]
    assert {r.outcome for r in many.results} == {"killed", "survived"}


def test_every_mutant_is_logged_once(tmp_path):
    automation, command, _ = _setup(tmp_path)
    lines = []
    report = mutate.run_mutation(automation, command, workdir=tmp_path / "work", jobs=3, log=lines.append)
    judged = [line for line in lines if line.split()[0] in {"killed", "survived", "invalid", "error"}]
    assert len(judged) == len(report.results)
    assert sorted(line.split()[1] for line in judged) == sorted(r.mutant.id for r in report.results)


def test_a_command_that_cannot_start_stops_the_run_even_with_jobs(tmp_path):
    automation, _, _ = _setup(tmp_path)
    with pytest.raises(SystemExit, match="Cannot run"):
        mutate.run_mutation(automation, ["/nonexistent/python", "-m", "pytest"], jobs=3, workdir=tmp_path / "work")


def test_jobs_below_one_is_an_error(tmp_path):
    automation, command, _ = _setup(tmp_path)
    with pytest.raises(SystemExit, match="jobs"):
        mutate.run_mutation(automation, command, jobs=0, workdir=tmp_path / "work")


def test_the_option_is_read_from_the_command_line():
    own, command = mutate.split_command(["lamp.yaml", "--jobs", "4", "--", "pytest"])
    assert own == ["lamp.yaml", "--jobs", "4"] and command == ["pytest"]
