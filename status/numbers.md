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
| Tests passing | 168 pass: 22 in `test_daylight_heartbeat.py`, 30 in `test_memory.py`, 12 in `test_motion_light.py`, 24 in `test_mutate.py`, 25 in `test_release.py`, 41 in `test_roadmap.py`, 14 in `test_status.py` | 2026-11-07 | `.venv/bin/python -m pytest -q` |
| `motion_light.yaml` mutants killed | 18 of 18 (the first run killed 16; the two survivors exposed a test gap that was then closed) | 2026-11-07 | the mutation command in `AGENTS.md` |
| `daylight_heartbeat.yaml` mutants killed | 27 mutants: 23 killed, 0 survived, 4 invalid, score 100 % (the first run killed 21 of 23; the two survivors exposed a test gap that was then closed) | 2026-11-07 | `mutate` on that blueprint with `tests/test_daylight_heartbeat.py` |
| Home Assistant, test package, Python | 2026.10.4, `pytest-homeassistant-custom-component==0.13.375`, 3.14 | 2026-11-07 | `requirements-dev.txt` |
| Package version | 0.1.0.dev0 (development version; no release yet) | 2026-11-07 | `ha_blueprint_test_harness/__init__.py` |
| Platforms the tests were run on | macOS only | 2026-11-07 | |
| CI on GitHub | never run. The YAML is valid and its commands ran locally under `bash`, including the failing case | 2026-11-07 | `.github/workflows/ci.yaml` |
| Release workflow | never run. The parts that can run locally (version check, changelog extraction, build) were run | 2026-11-07 | `.github/workflows/release.yaml` |
| Repository | local Git repository, no commits, no remote | 2026-11-07 | `git log`, `git remote -v` |
| Supported blueprint kinds | automation blueprints only | 2026-11-07 | README |
