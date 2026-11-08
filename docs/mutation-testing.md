# Mutation testing

Passing tests tell you the blueprint does what the tests check. They do not tell you whether the tests check enough. The mutation tool answers that: it breaks your blueprint in small ways, one at a time, and runs your tests against each broken copy. If the tests still pass, a test is missing.

## Run it

```sh
.venv/bin/python -m ha_blueprint_test_harness.mutate blueprints/automation/my_blueprint.yaml \
  -- .venv/bin/python -m pytest -q -x -p no:cacheprovider tests/test_my_blueprint.py
```

- The path before `--` is the blueprint to break.
- Everything after `--` is the test command, run once per broken copy. Use `-x` (stop at the first failure) so a killed mutant is found quickly.
- Your tests need **no change**: while the tool runs, `BlueprintEnv.start()` hands out the broken copy whenever a test asks for that blueprint file.
- Without `--`, the tool runs `python -m pytest -q -x -p no:cacheprovider` with the Python that started it.

| Option | Meaning |
| --- | --- |
| `--timeout S` | Seconds per test run (default 120). A run that hangs counts as killed. |
| `--jobs N` | Run `N` mutants at the same time (default 1). Each run is its own process with its own file, so the result is the same; the tests must not share files or ports. Measured on a Mac with 8 cores and 39 mutants: 110 s with 1, 52 s with 4, 42 s with 8, because every run loads Home Assistant again. A run that waits for a timeout counts against its `--timeout` while the machine is busy, so do not set `N` much higher than the number of cores. |
| `--fail-under PCT` | Exit with status 1 if the score is below `PCT` (0 to 100). For CI. |
| `--workdir DIR` | Write the broken copies to `DIR` and keep them (default: a temporary folder that is removed). |

Do not edit your tests or the blueprint while it runs: each mutant is tested with the files as they are on disk at that moment, so a run can mix old and new versions.

Before it breaks anything the tool checks that your tests pass on the original and on an unchanged copy that it read and wrote back itself. If either fails it stops and says so: fix the tests first.

The tool runs your tests many times (once per mutant) and prints the result only at the end, so a run takes minutes without any output: with 73 mutants and 56 tests about 3 minutes (measured by a test project on 2026-11-07). Run it in the background in CI. The number of mutants grows with the size of the blueprint: the three used in this project's tests have 8, 18 and 27.

## Automations written directly

The same tool breaks an automation written directly. Give it the file and, if the file is a list as `automations.yaml` is, the entry to break:

```sh
.venv/bin/python -m ha_blueprint_test_harness.mutate docs/examples/car_driver.yaml \
  -- .venv/bin/python -m pytest -q -x -p no:cacheprovider docs/examples/test_car_driver.py
.venv/bin/python -m ha_blueprint_test_harness.mutate automations.yaml --pick my_automation_id -- ...
```

- `--pick` takes the `id` or the `alias`. Without it, a list with several entries stops with a message; only the picked entry is broken, the others stay as they are.
- The test must start the automation from the **file** (`start_automation(path)`); a dict cannot be swapped for a broken copy.
- The kinds of change are the same as for a blueprint (they follow the keys `triggers`, `conditions`, `actions` and the templates). Measured on the two examples of this project: `car_driver.yaml` 20 of 20, `frost_warning.yaml` 9 of 10 (the survivor, `mode: single` to `restart`, changes nothing because the run ends at once).

## Read the result

A real run on the documentation example [`examples/button_light.yaml`](examples/button_light.yaml), before one test was added:

```text
8 mutants of button_light.yaml
killed    M001  actions[0]: drop {'choose': [...
...
survived  M006  actions[0].choose[0].sequence[0].target: remove 'target' from light.turn_off
...
killed 7, survived 1, invalid 0 (blueprint no longer loads, not counted), error 0
score 88% of the 8 loadable mutants
survivors (a test gap or an equivalent change; judge each one):
  M006  actions[0].choose[0].sequence[0].target: remove 'target' from light.turn_off
```

| Outcome | Meaning |
| --- | --- |
| **killed** | A test failed or hung. Your tests noticed the change. Good. |
| **survived** | Every test passed although the blueprint was broken. A gap in the tests, or a change that does not alter behaviour. |
| **invalid** | The broken blueprint no longer loads (`BlueprintLoadError`). It says nothing about your tests and is left out of the score. |
| **error** | The tests passed on the original blueprint, but a test run for one mutant exited with a code of 2 or more (pytest itself broke). Rare. A wrong test path or a program that cannot be started does not give this outcome: the tool stops before it breaks anything and exits with 1. |

The **score** is killed / (killed + survived). **Exit codes:** 0 fine; 1 the score is below `--fail-under`, or the tool stopped before it started (the tests already fail on the unchanged blueprint, which includes a wrong test path, or the test command cannot be started); 2 at least one mutant run ended in `error`.

## Reading a survivor

Each survivor needs a human look. The tool cannot tell a gap from a harmless change.

**Usually a gap.** In the example above the survivor `M006` removes the `target` from `light.turn_off`. The test checked that `light.turn_off` was called but not *what it was aimed at*, so a blueprint that switches off nothing passed. The fix is one assertion:

```python
# Both calls must be aimed at our light; a call without a target would switch off nothing.
assert [call.entity_ids for call in blueprint_env.calls] == [{LIGHT}, {LIGHT}]
```

After it, all 8 mutants are killed (score 100%). The same happened on Home Assistant's `motion_light` blueprint: the first run killed 16 of 18, and the two survivors showed that nothing tested a sensor that drops out while the light is on.

**Often: defaults nobody relies on.** The tool changes the default of an input (by +1 or to 0). It survives when every test passes the value explicitly. Either add a test that leaves the input out and checks the default, or decide the default is not part of the behaviour.

**Sometimes harmless.** Some changes have no effect in a real Home Assistant, so no test can catch them:

- a `mode: single` changed to `restart` when runs never overlap;
- a check that guards a situation that cannot occur (for example a state without a timestamp that Home Assistant always sets);
- a guard whose failure Home Assistant rejects anyway, for example `{{ light | length > 0 }}` changed to `>= 0` before an action with an empty target: nothing is called either way.

Write down why you accept such a survivor, for instance in a comment next to the blueprint, and do not set `--fail-under` to a value that this survivor makes impossible.

Make sure the test command runs tests that actually load this blueprint. If it runs unrelated tests, every mutant survives; the tool lists them but, without `--fail-under`, still exits with 0. Use `--fail-under` in CI so that this cannot go unnoticed.

A killed mutant only shows that *some* test failed, not that the test is a good one. A high score is necessary, not sufficient.

## What gets broken

| Mutation | What it does |
| --- | --- |
| `drop_item` | removes one trigger (if there are several), condition, action, `choose` branch, `then`/`else` step |
| `drop_key` | removes `from`, `to`, `for`, `above`, `below`, `after`, `before`, `after_offset`, `before_offset` from a trigger or condition, or `target`/`data` from an action |
| `swap_from_to` | swaps `from` and `to` |
| `action_swap` | `turn_on` <-> `turn_off`, `lock` <-> `unlock` |
| `mode` | `restart`/`queued`/`parallel` -> `single`, `single` -> `restart` |
| `number` | a `delay` or an input default: +1, or 0 |
| `bool` | flips a boolean (also input defaults) |
| `template` | in Jinja strings: each spaced comparison (`<=` <-> `<`, `==` <-> `!=`), `and` <-> `or`, `not` removed, `true` <-> `false` |

**Not mutated:** numbers inside templates, the `blueprint:` header (except input defaults) and the bodies of `choose` branches beyond dropping items. A score of 100% therefore does not mean the blueprint is fully tested.

## In CI

Add the command to your workflow with `--fail-under` (see [Configuring your project](configuring-your-project.md#run-it-in-github-actions)). Start with the score you have and raise it as you close gaps; 100 is a good goal and a demanding start.

The tool passes your environment on to the test command, minus its own `HA_BLUEPRINT_TEST_HARNESS_*` variables. Do not run it with secrets in the environment on a blueprint or tests you do not trust ([`SECURITY.md`](../SECURITY.md)).

Without a command after `--` the tool runs `pytest` in the current directory, which loads that directory's `conftest.py`; run it only on files you have read. Give `--workdir` an empty folder: the tool stops if it finds `control.yaml` or `M001.yaml`, ... from an earlier run there, and it never writes through a link. The tool refuses a file with YAML aliases (`*name`, they are written out in full for every mutant and can make a run last minutes) and a file above 1 MB; write the values out instead.
