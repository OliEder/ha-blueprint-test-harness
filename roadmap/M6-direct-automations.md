---
id: M6
title: Direct automations - test an automation without wrapping it as a blueprint
description: Load an automation that is written directly (as in automations.yaml or the UI's YAML view), mock services that return a response, and run the mutation tool on it.
metadata:
  type: roadmap-item
  depends_on: []
  applies_to: [ha_blueprint_test_harness/env.py, ha_blueprint_test_harness/mutate.py, memory/automations-via-blueprint-wrapper.md, docs/writing-tests.md]
  updated: 2026-11-08
---

**Why.** Found on 2026-11-08 on a real heater automation: giving its configuration a blueprint header already makes it testable, and it exposed a real defect (a bare `false` that arrives as text). That is a working first version; the gaps are in `memory/automations-via-blueprint-wrapper.md`. M11 (done) already lets a test read the variables and branches of a run.

**Goal.** A person with an automation in `automations.yaml` (or copied from the UI's YAML view) can test it, and measure the tests with the mutation tool, without editing the automation.

**Scope**
- **Load an automation directly.** `start_automation(config)` takes the configuration as a dict or a path to a YAML file (a single automation, or one entry of a list picked by `id` or alias), with the same options as `start()` (`states`, `services`, `effects`, `components`, `config_entries`, `when`). No blueprint header, no copy of the file changed.
- **Services that return a response.** `responses={"weather.get_forecasts": {...}}` (a value or a function of the call) registers the service with response support, so `response_variable` works. Today the test has to register such a service by hand, and a run stops when it is missing even with `continue_on_error`.
- **Mutation testing for automations.** The mutation tool accepts an automation file as well as a blueprint and mutates its triggers, conditions, actions and templates the same way.
- **Documentation.** A section "Test an automation you wrote directly" in `docs/writing-tests.md` with a runnable example on an original automation (not on a real one: entity names stay private), and a line in the README and `docs/index.md` saying that automations are supported.

**Done when**
- A test runs an automation from a dict and one from a file, without a blueprint header, and a service with a response works.
- The mutation tool runs on that example automation and reports a score; the example reaches the agreed score.
- `memory/automations-via-blueprint-wrapper.md` is replaced by the documentation (the wrapper stays as a one-line tip for older versions, if still useful).

**Not included.** Scripts and helpers (milestone M12), script and template blueprints (M5). Reading `automations.yaml` from a real instance: the harness does not talk to one.
