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
| Tests passing | 187 pass: 3 in `docs/examples/test_logged_problems.py`, 5 in `docs/examples/test_event_entity_light.py`, 6 in `docs/examples/test_button_light.py`, 2 in `docs/examples/test_motion_light_timing.py`, 22 in `test_daylight_heartbeat.py`, 33 in `test_memory.py`, 12 in `test_motion_light.py`, 24 in `test_mutate.py`, 25 in `test_release.py`, 41 in `test_roadmap.py`, 14 in `test_status.py` | 2026-11-07 | `.venv/bin/python -m pytest -q` |
| `motion_light.yaml` mutants killed | 18 of 18 (the first run killed 16; the two survivors exposed a test gap that was then closed) | 2026-11-07 | the mutation command in `AGENTS.md` |
| `docs/examples/button_light.yaml` mutants killed | 8 of 8, score 100 % (the first run killed 7 of 8; the survivor showed that no test checked the target of `light.turn_off`; it is the worked example in `docs/mutation-testing.md`) | 2026-11-07 | `mutate` on that blueprint with `docs/examples/test_button_light.py` |
| `docs/examples/event_entity_light.yaml` mutants killed | 11 of 11, score 100 % (the first run killed 9 of 11; the two survivors were again the missing check of the call's target) | 2026-11-07 | `mutate` on that blueprint with `docs/examples/test_event_entity_light.py` |
| `daylight_heartbeat.yaml` mutants killed | 27 mutants: 23 killed, 0 survived, 4 invalid, score 100 % (the first run killed 21 of 23; the two survivors exposed a test gap that was then closed) | 2026-11-07 | `mutate` on that blueprint with `tests/test_daylight_heartbeat.py` |
| Home Assistant, test package, Python | 2026.10.4, `pytest-homeassistant-custom-component==0.13.375`, 3.14 | 2026-11-07 | `requirements-dev.txt` |
| Package version | 0.1.0 prepared on branch `release/0.1.0` (not merged, not tagged, not published) | 2026-11-07 | `ha_blueprint_test_harness/__init__.py` |
| Built package | `python -m build` gives the wheel and the source archive of 0.1.0; `twine check` passes for both | 2026-11-07 | `.venv/bin/python -m build && .venv/bin/twine check dist/*` |
| Install from the wheel into a fresh environment | works with the two configuration files described in `docs/getting-started.md`; without `asyncio_mode = auto` or the plugin in `conftest.py` the first test errors; Home Assistant 2026.10.4 was resolved | 2026-11-07 | install the wheel into a new venv, copy the example from the README |
| Platforms the tests were run on | macOS (locally) and Ubuntu (GitHub Actions, `ubuntu-latest`) | 2026-11-07 | the `CI` runs on GitHub |
| CI on GitHub | green on the first run: `tests` (168 pass on Home Assistant 2026.10.4) and `mutation` (100 % on both blueprints) | 2026-11-07 | `gh run list --repo OliEder/ha-blueprint-test-harness` |
| Release workflow | never run. The parts that can run locally (version check, changelog extraction, build) were run | 2026-11-07 | `.github/workflows/release.yaml` |
| Repository | public: https://github.com/OliEder/ha-blueprint-test-harness | 2026-11-07 | `git remote -v` |
| Supported blueprint kinds | automation blueprints only | 2026-11-07 | README |
