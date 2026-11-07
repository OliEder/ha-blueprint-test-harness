---
id: M3
title: Compatibility layer - every Home Assistant internal behind one module
description: Put every use of a Home Assistant internal behind one module and add canary tests, so that a new version breaks one known place.
metadata:
  type: roadmap-item
  depends_on: []
  applies_to: [ha_blueprint_test_harness/env.py, memory/scope-and-version-compatibility.md]
  updated: 2026-11-07
---

**Goal.** When a new Home Assistant version changes something the harness relies on, the change shows up in one module and one failing canary test names it.

**Scope**
- **One place for internals.** Imports of Home Assistant internals and of the pytest plugin, and every assumption about their behaviour, live in a single module. The rest of the harness calls that module.
- **Canary tests.** One small test per internal the harness relies on, for example firing timers, replacing the config folder, reading `last_reported`, setting up a component. On a new version they fail first and say which one moved.
- **Start with an inventory** of the internals used today, before moving anything.

**Done when**
- No module in `ha_blueprint_test_harness/` other than the compatibility module imports `homeassistant` or the pytest plugin; a test checks this.
- Each internal on the inventory has a canary test.
- A simulated change of one internal makes exactly the matching canary fail.

**Not included.** Running on several versions at once (M4). M3 comes first on purpose: a matrix over versions is worth running only when a version change breaks one known place.
