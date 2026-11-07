---
id: M2
title: Broader reference set - fixture blueprints for more trigger kinds and actions
description: Add original fixture blueprints for more trigger kinds and action types, each with tests and a mutation score, so that the harness and the mutation tool are exercised beyond state and time triggers.
metadata:
  type: roadmap-item
  depends_on: []
  applies_to: [tests/blueprints/daylight_heartbeat.yaml, tests/test_daylight_heartbeat.py, memory/equivalent-mutants.md]
  updated: 2026-11-07
---

**Goal.** The harness and the mutation tool are shown to work on more than state and time-pattern triggers. Every fixture is an original blueprint under `tests/blueprints/`, so that nothing depends on files outside the repository.

**Scope.** Fixtures for event triggers, numeric-state triggers (`above`, `below`, `for`), zone triggers, `choose` with a `default`, `repeat` and `wait_template`. For each: tests through `blueprint_env`, a mutation run, and a judgement of every survivor (a test, or an equivalent mutant recorded in `memory/equivalent-mutants.md`). Where the mutation tool lacks an operator that a fixture needs, add the operator with a unit test.

**Done when**
- At least three more fixtures exist, each with tests.
- Each fixture has a mutation score of at least 90 % (proposal, to be agreed), not counting documented equivalent mutants.
- The CI mutation job runs every fixture.

**Not included.** Script and template blueprints (M5).
