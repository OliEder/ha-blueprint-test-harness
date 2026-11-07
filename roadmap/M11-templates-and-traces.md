---
id: M11
title: Templates and traces - test a blueprint's templates and see how a run went
description: Render a template against simulated states, read the trace of the last run and provide config entries, so that template checks done by hand in an instance can be done in tests.
metadata:
  type: roadmap-item
  depends_on: []
  applies_to: [ha_blueprint_test_harness/env.py, docs/writing-tests.md, docs/examples/button_light.yaml]
  updated: 2026-11-07
---

**Why.** Found on 2026-11-07 on a real blueprint (an automation blueprint with Jinja in `variables`, `choose` sequences and a call of a custom integration's service). The harness ran it unchanged, but only end to end: a value that never reaches a service payload (a validity flag, a computed total) cannot be looked at, and the check that its author does by hand in the instance's template tool has no counterpart in a test.

**Goal.** What is done by hand in an instance can be done in a test: evaluate a template, see the evaluated variables of a run, and use the template functions that need a config entry.

**Scope**
- `render(template, variables=None)` on `BlueprintEnv`: evaluates a template string against the simulated states.
- `last_trace()`: the trace of the last automation run (evaluated variables, the chosen path). The `trace` component is already loaded in the harness; reading it uses Home Assistant internals, so it sits in one small function (the rule of M3).
- `config_entries=` for `start()`, built on `MockConfigEntry` of the test package, for functions such as `config_entry_id` and `config_entry_attr`.
- A section "Test the templates" in `docs/writing-tests.md` with runnable examples on an original fixture, not on someone else's blueprint.

**Done when**
- A test asserts an evaluated variable of a run through `last_trace()`.
- A test renders a template with simulated states, and one uses a config entry.
- Each helper has a runnable example in `docs/examples/` and a canary test for the internal it uses.

**Not included.** Script entities and script blueprints (M5). Branch coverage (M7) builds on `last_trace()`.
