---
name: mutation-outcomes-killed-invalid
description: What killed, survived, invalid and error mean in a mutation run, and why invalid mutants are left out of the score.
metadata:
  type: fact
  applies_to: [ha_blueprint_test_harness/mutate.py, ha_blueprint_test_harness/env.py]
  checked: 2026-11-07
---

A timeout counts as killed: a mutant that makes a script hang is noticed. "Invalid" means the blueprint no longer produced a working automation (`BlueprintLoadError`). It is left out of the score because it says nothing about the tests.

**Why:** the load check exists because Home Assistant logs a bad blueprint and carries on instead of failing.

**How to apply:** when the invalid count rises after a change, look at what the new mutants break at load time. A blueprint that fails to load for almost every mutant points at a wrong operator.
