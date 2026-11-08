---
name: equivalent-mutants
description: Mutants that survive without being a test gap (changes with no effect in real Home Assistant); add new ones here with the reason.
metadata:
  type: fact
  applies_to: [ha_blueprint_test_harness/mutate.py]
  checked: 2026-11-07
---

- A measurement report time in the future, and a state without `last_reported`: unreachable in real Home Assistant, so a surviving mutant there is not a test gap (seen when mutating a blueprint that checks the age of sensor readings).
- `mode: single` to `restart` can be equivalent when runs never overlap (seen again on `docs/examples/window_heater.yaml`, whose actions finish at once).

**Why:** a survivor is either a gap or a change with no effect, and only a person can tell which.

**How to apply:** record a new equivalent mutant here, with the reason, before accepting it as a survivor.
