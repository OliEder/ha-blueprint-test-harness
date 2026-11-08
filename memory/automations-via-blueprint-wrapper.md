---
name: automations-via-blueprint-wrapper
description: A directly written automation can already be tested today by putting a blueprint header on its configuration; what is missing is a proper API (M6).
metadata:
  type: observation
  applies_to: [ROADMAP.md, roadmap/M6-direct-automations.md, ha_blueprint_test_harness/env.py]
  checked: 2026-11-08
---

Found 2026-11-08 on a real automation (a heater control with Jinja in `variables`, `choose` and a forecast service call). Add `blueprint: {name: ..., domain: automation}` to the automation's configuration (drop `id`, `alias`, `description`), save it as a YAML file and pass it to `BlueprintEnv.start()` without inputs. It runs unchanged on the real Home Assistant core. Six scenarios (cold room, warm room, window open with the heater off and on, off-grid cold and warm) found a real defect: a bare `false` in a template branch arrives as the text "false", which counts as true.

**Why this matters:** it is a working minimal version of M6 for automations without any change to the harness. It also shows what M6 still has to add.

**Gaps seen:** a service that returns a response (`weather.get_forecasts`) cannot be mocked through `services=`; the test had to register it by hand with `supports_response`, and without it the run stops (`continue_on_error` does not catch a missing service). The evaluated variables of a run can now be read with `last_trace()` (M11, done 2026-11-08), which shows the text "false" directly. A direct `start_automation(config)` would remove the manual wrapping.

**How to apply:** when asked whether the harness can test an automation, say yes with this wrapper, and name the gaps. Do not call it supported until M6 is done.
