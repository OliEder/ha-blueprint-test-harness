---
name: numbers
description: Test counts, mutation scores, versions and CI state, each with its date and the command that reproduces it.
metadata:
  type: status
  applies_to: [requirements-dev.txt, .github/workflows/ci.yaml, tests/test_motion_light.py, tests/test_daylight_heartbeat.py, tests/test_mutate.py, tests/test_memory.py, tests/test_status.py, tests/test_roadmap.py, tests/test_release.py, ha_blueprint_test_harness/__init__.py]
  updated: 2026-11-07
---

Write a number here with its date and command, and nowhere else without both.

| What | Value | Date | How to reproduce |
| --- | --- | --- | --- |
| Tests passing | 241 pass on 2026-11-08 (M6: 12 in `tests/test_start_automation.py`, 6 in `tests/test_mutate_automation.py`, 12 in `docs/examples/test_car_driver.py`, 8 in `docs/examples/test_frost_warning.py`, fewer in `test_roadmap.py` because the M6 file is gone; the suite takes about 20 s because one test runs the mutation tool on a small project); 209 passed before it (with the M6 file: `test_roadmap.py` has more cases); 204 passed before that (with M11: 11 in `docs/examples/test_window_heater.py`, 1 in `test_trace_canary.py`, fewer in `test_roadmap.py` because the M11 file is gone); before that 192 pass: 3 in `docs/examples/test_logged_problems.py`, 5 in `docs/examples/test_event_entity_light.py`, 6 in `docs/examples/test_button_light.py`, 2 in `docs/examples/test_motion_light_timing.py`, 22 in `test_daylight_heartbeat.py`, 36 in `test_memory.py`, 12 in `test_motion_light.py`, 24 in `test_mutate.py`, 25 in `test_release.py`, 43 in `test_roadmap.py`, 14 in `test_status.py` | 2026-11-07 | `.venv/bin/python -m pytest -q` |
| `motion_light.yaml` mutants killed | 18 of 18 (the first run killed 16; the two survivors exposed a test gap that was then closed) | 2026-11-07 | the mutation command in `AGENTS.md` |
| `docs/examples/button_light.yaml` mutants killed | 8 of 8, score 100 % (the first run killed 7 of 8; the survivor showed that no test checked the target of `light.turn_off`; it is the worked example in `docs/mutation-testing.md`) | 2026-11-07 | `mutate` on that blueprint with `docs/examples/test_button_light.py` |
| `docs/examples/event_entity_light.yaml` mutants killed | 11 of 11, score 100 % (the first run killed 9 of 11; the two survivors were again the missing check of the call's target) | 2026-11-07 | `mutate` on that blueprint with `docs/examples/test_event_entity_light.py` |
| `docs/examples/window_heater.yaml` mutants killed | 21 of 22, score 95 % (the first run killed 10 of 22 because the tests only showed the API; the survivor `mode restart -> single` is equivalent) | 2026-11-08 | `mutate docs/examples/window_heater.yaml -- .venv/bin/python -m pytest -q -x docs/examples/test_window_heater.py` |
| `docs/examples/car_driver.yaml` mutants killed | 20 of 20, score 100 % (an automation written directly; the first run on the maintainer's real version killed 15 of 20: no test checked the trigger's `from`/`to`, the target of the writes or the `from: home` of the wait) | 2026-11-08 | `mutate docs/examples/car_driver.yaml -- .venv/bin/python -m pytest -q -x docs/examples/test_car_driver.py` |
| `docs/examples/frost_warning.yaml` mutants killed | 9 of 10, score 90 % (the survivor `mode single -> restart` is equivalent: the run ends at once) | 2026-11-08 | `mutate docs/examples/frost_warning.yaml -- .venv/bin/python -m pytest -q -x docs/examples/test_frost_warning.py` |
| `daylight_heartbeat.yaml` mutants killed | 27 mutants: 23 killed, 0 survived, 4 invalid, score 100 % (the first run killed 21 of 23; the two survivors exposed a test gap that was then closed) | 2026-11-07 | `mutate` on that blueprint with `tests/test_daylight_heartbeat.py` |
| Home Assistant, test package, Python | 2026.11.0 with `pytest-homeassistant==2026.11.0`, 3.14.3 (209 tests pass, fresh environment); also 2026.10.4 with `pytest-homeassistant-custom-component==0.13.375`, 3.14.3 (209 tests pass) | 2026-11-08 | `requirements-dev.txt`, `requirements-dev-custom-component.txt` |
| Package version | 0.3.0 on the branch `docs/m6-direct-automations` (release commit, not yet merged or tagged). 0.2.0 was released as `v0.2.0` on commit `ca56157`; 0.1.0 as `v0.1.0` on `4ab973f` | 2026-11-07 | `ha_blueprint_test_harness/__init__.py`, `git tag` |
| Built package | `python -m build` gives the wheel and the source archive of 0.1.0; `twine check` passes for both | 2026-11-07 | `.venv/bin/python -m build && .venv/bin/twine check dist/*` |
| Install from the wheel into a fresh environment | works with the two configuration files described in `docs/getting-started.md`; without `asyncio_mode = auto` or the plugin in `conftest.py` the first test errors; Home Assistant 2026.10.4 was resolved | 2026-11-07 | install the wheel into a new venv, copy the example from the README |
| Platforms the tests were run on | macOS (locally) and Ubuntu (GitHub Actions, `ubuntu-latest`) | 2026-11-07 | the `CI` runs on GitHub |
| CI on GitHub | green on the pull request that prepared 0.1.0: `tests` (187 pass on Home Assistant 2026.10.4, Ubuntu) and `mutation` (`motion_light` 18 of 18, fixture 23 of 23, 100 %) | 2026-11-07 | `gh run list --repo OliEder/ha-blueprint-test-harness` |
| Release workflow | ran twice, both green: a dry run started by hand on `main` (run 42412289809, no release created) and the real run for the tag `v0.1.0` (run 42412700994), which created the draft release; the draft was published by hand | 2026-11-07 | `gh run list --workflow release.yaml --repo OliEder/ha-blueprint-test-harness` |
| Release `v0.1.0` | published 2026-11-07 with the wheel (20 480 bytes, sha256 starts `dc7663d1a7824754`) and the source archive (31 690 bytes, sha256 starts `8d5908e6c47e6b14`); both answer without login; the requirement line in `docs/configuring-your-project.md` installs 0.1.0 into a fresh environment and the example test passes | 2026-11-07 | `gh release view v0.1.0 --repo OliEder/ha-blueprint-test-harness` |
| Repository | public: https://github.com/OliEder/ha-blueprint-test-harness | 2026-11-07 | `git remote -v` |
| Supported kinds | automation blueprints and automations written directly (M6, unreleased) | 2026-11-07 | README |
