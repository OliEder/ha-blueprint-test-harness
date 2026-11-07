---
name: yaml-round-trip-quirks
description: Two things in the mutation tool's YAML handling that look like bugs but are not (quoted !input, unquoted off).
metadata:
  type: pitfall
  applies_to: [ha_blueprint_test_harness/mutate.py]
  checked: 2026-11-07
---

- The mutation tool writes `!input 'name'` with quotes. In YAML that equals `!input name`; Home Assistant loads it the same way.
- PyYAML reads an unquoted `off` as `false`. Blueprints quote `"off"`/`"on"` for this reason; the tool keeps whatever the file has.

**Why:** the control run (tests on the unchanged, re-written blueprint) proves the first before any mutant runs.

**How to apply:** do not "fix" the quotes. If the control run fails, look at the round trip first, not at the tests.
