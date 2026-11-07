---
name: settle-instead-of-block-till-done
description: Why the harness runs the event loop in settle() and never calls hass.async_block_till_done(); what to do when a long chain of actions is not finished.
metadata:
  type: pitfall
  applies_to: [ha_blueprint_test_harness/env.py]
  checked: 2026-11-07
---

`hass.async_block_till_done()` waits for every open task. A blueprint script that waits for a trigger (`wait_for_trigger`) or sits in a `delay` keeps a task open, so the call never returns and the test hangs.

**Why:** Home Assistant's own `motion_light` test says the same ("Can't block till done because delay is active") and waits 10 event-loop iterations. `settle()` waits 20.

**How to apply:** use `settle()`, `set_state()`, `fire_event()` and `advance()`. If a long chain of actions is not finished after one call, call `settle()` again in the test. Do not switch to `async_block_till_done()`.
