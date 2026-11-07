# ha-blueprint-test-harness — instructions for agents

A pytest-based **testing** harness for Home Assistant automation blueprints. It loads the real blueprint YAML as an automation, feeds it simulated states, events and time, records the services it calls, and ships a mutation tool that breaks the blueprint in small ways to see whether the tests notice. Prototype, not released, not an official Home Assistant project.

Today it covers automation blueprints. The direction is wider (other blueprint kinds, automations, scripts, helpers, in the long run all kinds of extensions) and every kind must work on several Home Assistant versions; see `ROADMAP.md`. Nothing in this repository may depend on an agent: humans and CI use it the same way.

## Start every session here

1. [`STATUS.md`](STATUS.md): a short index with the project map. Read the map first, then only the files the task needs. Current numbers, open items and commands are in `status/`; open only the file you need.
2. [`ROADMAP.md`](ROADMAP.md): the direction and a table of milestones with their states. If your task belongs to a milestone, open its file in `roadmap/`; read the log in `roadmap/log/` only for the recent past.
3. [`MEMORY.md`](MEMORY.md): an index of decisions and facts the code does not record, one line each. Read the index, then open only the entries in `memory/` that match your task.
4. [`VISION.md`](VISION.md) only when the task is about the long-term direction. It is not a work list.

No file here is large. `ha_blueprint_test_harness/mutate.py` is the longest (about 420 lines, a third of it comments).

## Rules

1. **A person is accountable.** Whoever runs an agent answers for what it changes and claims.
2. **Report only what ran.** Name the command and the result. Say what you did not run: another operating system, GitHub Actions, a real Home Assistant instance, a real device. A green harness run is not a statement about a real instance.
3. **Mocked services check nothing.** A service in `services=` records any data. A parameter that changed in the real integration goes unnoticed. Never describe a harness result as proof about an integration.
4. **Do not weaken a test to kill a mutant or to turn a run green.** Judge each survivor on its own: add a test, or record in `memory/equivalent-mutants.md` why the change is equivalent (mutant, change, reason). Do not remove a mutation operator because it produces survivors.
5. **Never use `hass.async_block_till_done()` in the harness.** A script waiting for a trigger or sitting in a `delay` keeps a task open, so it never returns. Use `settle()` (see `memory/settle-instead-of-block-till-done.md`).
6. **The Home Assistant version is pinned** in `requirements-dev.txt`. Raising it is its own change: run the tests and the mutation run on the new version and update `STATUS.md`.
7. **Keep real systems out of the repository.** No entity IDs, serial numbers, locations, hostnames, tokens or screenshots from a real instance. Fixtures are synthetic. Readings from a real instance stay in the conversation; a finding may go into a `memory/` entry only without names.
8. **Licences.** Do not copy code from another project unless its licence allows it and you record it. Home Assistant core's tests (Apache-2.0) are a source of patterns, not of pasted code. A repository without a licence is all rights reserved: do not copy it. Check a dependency's licence before adding it.
9. **Every class, function and method has a short comment above it** that says in plain words what it does, so a person can read a file top to bottom. Keep the comments true when you change the code.
10. **English only** in the repository: code, comments, documents.
11. **Stop and ask before:** publishing, creating or pushing to a remote, opening issues or pull requests, releases, spending money, destructive git, or touching a real Home Assistant instance beyond reading. Do not post anything on a person's behalf without a go-ahead. An agent may prepare a release commit and draft the notes; it does not create or push a tag and does not publish. `main` is protected on GitHub: an agent works on a branch and does not push to `main`. The maintainer's credentials bypass the protection, so this rule is what holds. Keep working on everything else.
12. **Real instances are read-only.** If a Home Assistant instance is reachable (for example through an MCP server), read; write only with explicit approval and a way back. Never copy a password or token.
13. **How tests are written here.** Arrange, act, assert, in that order. Every interaction with the network or the file system gets at least two mocked failure cases. Where input is parsed, test the boundaries: zero, negative numbers, very long strings. When two modules start exchanging data across a new interface, add a test of that seam. A new mutation operator comes with a unit test in `tests/test_mutate.py` and a row in the README table.
14. **CI changes are their own change.** Check the YAML and run its commands locally. Say that it has not run on GitHub until it has.
15. **The documents are part of the work.** After a larger piece of work walk the table in "Keeping the documents current" and update what the work changed. Before relying on a claim in them that names a file, command or number, check it.

## Quality gate before every commit

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m ha_blueprint_test_harness.mutate \
  "$(.venv/bin/python -c "import pathlib, homeassistant.components.automation as a; print(pathlib.Path(a.__file__).parent / 'blueprints' / 'motion_light.yaml')")" \
  --fail-under 100 -- .venv/bin/python -m pytest -q -x tests/test_motion_light.py
```

This is what `.github/workflows/ci.yaml` runs. Set-up: `uv venv --python 3.14 .venv && uv pip install --python .venv/bin/python -r requirements-dev.txt`.

## Layout

| Path | What it is |
| --- | --- |
| `ha_blueprint_test_harness/env.py` | `BlueprintEnv`: load a blueprint, set states, fire events, advance time, record service calls |
| `ha_blueprint_test_harness/mutate.py` | The mutation tool (`python -m ha_blueprint_test_harness.mutate`) |
| `ha_blueprint_test_harness/pytest_plugin.py` | The `blueprint_env` fixture |
| `conftest.py` | Loads the plugin; tells Home Assistant's test setup that lingering timers are expected |
| `tests/test_motion_light.py` | Home Assistant's own `motion_light.yaml`, the reference user of the harness |
| `tests/test_daylight_heartbeat.py`, `tests/blueprints/daylight_heartbeat.yaml` | Second user: a small original fixture blueprint with a time pattern, sun conditions and a `choose` block |
| `tests/test_mutate.py` | Tests of the mutation tool itself |
| `tests/test_memory.py`, `tests/test_status.py`, `tests/test_roadmap.py`, `tests/test_release.py` | Check that each index and its files agree, that files they name exist, and that version, changelog and public API are consistent |
| `MEMORY.md`, `memory/` | The memory: an index and one short file per entry |
| `STATUS.md`, `status/` | The status: an index with the map by task, and files for numbers, open items and commands |
| `ROADMAP.md`, `roadmap/` | The plan: an index table, one file per milestone with content, and a monthly log |
| `tools/release_info.py` | Reads the version, extracts changelog sections and checks release tags; used by the release workflow and by tests (standard library only) |
| `.github/workflows/ci.yaml` | Tests, then mutation runs on `motion_light.yaml` and on the fixture blueprint |
| `.github/workflows/release.yaml` | Builds a draft GitHub release from a version tag |
| `RELEASING.md`, `CHANGELOG.md`, `pyproject.toml` | Versioning policy and release steps; what changed per version; the package definition |

## Writing a test for a blueprint

```python
async def test_example(blueprint_env):
    await blueprint_env.start("path/to/blueprint.yaml", {"some_input": "value"},
                              states={"binary_sensor.x": "off"}, services=["light.turn_on"])
    await blueprint_env.set_state("binary_sensor.x", "on")
    await blueprint_env.advance(120)
    assert [call.name for call in blueprint_env.calls] == ["light.turn_on"]
```

Use `components=["sun"]` and `when=<datetime>` for blueprints with sun conditions. After writing tests, run the mutation tool on the blueprint and look at every survivor.

## Keeping the documents current

One home for each kind of information. Other files link to it and do not copy it, because copies drift apart.

| Kind of information | Home | Update when | How |
| --- | --- | --- | --- |
| Where things are, which files a task needs | `STATUS.md` (index and map) | a file moves, a new area appears, a status file is added or removed | edit the map row; every path in the map must exist (`tests/test_status.py`) |
| Numbers: tests, mutation scores, versions, CI state | `status/numbers.md` | after any run that changes one | write the number with its date and command; do not quote a number elsewhere without both |
| Open items | `status/open.md` | an item is found, blocked or done | delete a done item; one the size of a milestone gets a line in the roadmap progress log |
| Commands and local quirks | `status/practical.md` | a command or a quirk changes | |
| The plan: direction, milestones, and the state of each | `ROADMAP.md` (its table is the only place for a state) | a milestone changes state or the scope changes | edit the row; a state is one of `open`, `active`, `done`, `idea`, `direction` |
| The detail of a milestone you work on or are about to | `roadmap/Mn-*.md` | its goal, scope or "done when" changes | no state in the file; delete the file when the milestone is done and keep what is still true in `memory/` or the README |
| What happened | `roadmap/log/YYYY-MM.md` | a larger piece of work lands | one dated line, newest first; a new month starts a new file and `ROADMAP.md` links it |
| A fact, decision or lesson that the code does not say | an entry in `memory/` plus one line in the `MEMORY.md` index | you learn something a later reader would have to rediscover | one fact per file with front matter; name the files it applies to; split an entry past 40 lines |
| An idea that is not accepted, or a problem a harness could prevent | `VISION.md` | it comes up | a dated line: what happened, not what is assumed |
| What changed for users, per version | `CHANGELOG.md` | any change a user can see (API, command line, behaviour, supported versions) | one line under `Unreleased` in the right group |
| How versions and releases work | `RELEASING.md` | the policy or the public API changes | keep the API list in step with `__all__` (`tests/test_release.py` checks it) |
| How to use the tool | `README.md` | the API, a command or the mutation table changes | |
| What running the tool executes | `SECURITY.md` | that changes | |

Rules:

- **Which home?** A number or state that changes goes to `status/`. A plan goes to `ROADMAP.md`. A reason, a decision or a fact goes to `memory/`. An idea that is not accepted goes to `VISION.md`. Rules for working here go into this file.
- **Dates.** A document with front matter carries a date (`checked` or `updated`). Change it when you re-verify or edit the content, and only then.
- **Delete what is wrong or done.** Do not annotate it; history is in git.
- **Index lines say when to read.** Every line in `MEMORY.md` and in the status list of `STATUS.md` ends in a sentence that starts with "read" and names the situation.
- **At the end of a larger piece of work** walk the table top to bottom and ask of each row whether the work changed it. Then run the tests: `tests/test_memory.py`, `tests/test_status.py` and `tests/test_roadmap.py` catch missing index lines, broken links, entries that name files that are gone, a map that points nowhere, and a milestone table that does not match its files. They cannot tell whether a line is true or helpful; that stays with you.
- **Before relying on a claim** in these files that names a file, a command or a number, check it: open the file, run the command.

See [`SECURITY.md`](SECURITY.md) for what running this tool executes.
