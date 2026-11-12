"""The mutation tool can run one part of the mutants (`--shard I/N`), so a long run can be split over several CI machines.
A fake test command stands in for pytest, so these tests are fast."""

import pytest

from ha_blueprint_test_harness import mutate

from test_mutate_jobs import _setup


# The ids of the mutants one run judged.
def _ids(automation, command, folder, shard):
    report = mutate.run_mutation(automation, command, workdir=folder, shard=shard, log=lambda _: None)
    return [result.mutant.id for result in report.results]


def test_the_shards_together_cover_every_mutant_exactly_once(tmp_path):
    automation, command, _ = _setup(tmp_path)
    everything = _ids(automation, command, tmp_path / "all", (1, 1))
    parts = [_ids(automation, command, tmp_path / f"part{i}", (i, 3)) for i in (1, 2, 3)]
    assert sorted(sum(parts, [])) == sorted(everything)
    assert len(everything) > 3 and all(parts)


def test_a_shard_keeps_the_ids_of_the_whole_run(tmp_path):
    automation, command, _ = _setup(tmp_path)
    everything = _ids(automation, command, tmp_path / "all", (1, 1))
    assert _ids(automation, command, tmp_path / "second", (2, 4)) == everything[1::4]


def test_the_shard_is_named_in_the_first_line(tmp_path):
    automation, command, _ = _setup(tmp_path)
    lines = []
    mutate.run_mutation(automation, command, workdir=tmp_path / "work", shard=(2, 3), log=lines.append)
    assert "(shard 2/3)" in lines[0]


@pytest.mark.parametrize("shard", [(0, 3), (4, 3), (1, 0), (-1, 2)])
def test_a_shard_outside_the_range_is_an_error(tmp_path, shard):
    automation, command, _ = _setup(tmp_path)
    with pytest.raises(SystemExit, match="shard"):
        mutate.run_mutation(automation, command, shard=shard, workdir=tmp_path / "work")


@pytest.mark.parametrize("text, expected", [("1/1", (1, 1)), ("2/4", (2, 4)), ("10/12", (10, 12))])
def test_the_option_text_is_read(text, expected):
    assert mutate.parse_shard(text) == expected


@pytest.mark.parametrize("text", ["0/4", "5/4", "2", "a/b", "2/", "-1/2", "2/4/6"])
def test_a_wrong_option_text_is_refused(text):
    import argparse
    with pytest.raises(argparse.ArgumentTypeError):
        mutate.parse_shard(text)
