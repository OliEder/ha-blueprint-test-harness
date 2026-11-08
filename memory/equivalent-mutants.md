---
name: equivalent-mutants
description: Mutants that survive without being a test gap (changes with no effect in real Home Assistant); add new ones here with the reason.
metadata:
  type: fact
  applies_to: [ha_blueprint_test_harness/mutate.py]
  checked: 2026-11-08
---

- A measurement report time in the future, and a state without `last_reported`: unreachable in real Home Assistant, so a surviving mutant there is not a test gap (seen when mutating a blueprint that checks the age of sensor readings).
- `mode: single` to `restart` can be equivalent when runs never overlap (seen again on `docs/examples/window_heater.yaml`, whose actions finish at once).
- `>` to `>=` on a value that is multiplied by zero or only matters above zero (`report_age > 0` next to a product with the age, `soc_raw > 0` when the corrected level is 0 either way, `range_raw > 0` for a product that is 0 at 0): same result at the boundary (seen on `tests/automations/range_charging.yaml`, 3 mutants).
- `mode: queued` or `single` to the other one when every run ends at once (a mocked notify returns immediately), so runs never overlap (seen on `tests/automations/humidity_warning.yaml` and `range_charging.yaml`).
- A bound that the value can never cross: `below: 360` or `above: 0` on a sun azimuth, which is always between 0 and 360 (seen on `tests/automations/sun_shutter.yaml`, 2 mutants).

**Why:** a survivor is either a gap or a change with no effect, and only a person can tell which.

**How to apply:** record a new equivalent mutant here, with the reason, before accepting it as a survivor.
