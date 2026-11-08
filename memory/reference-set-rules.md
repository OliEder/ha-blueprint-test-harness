---
name: reference-set-rules
description: How the reference automations are made and judged (derived from real ones, floor = measured score rounded down), and which constructs still have no fixture.
metadata:
  type: decision
  applies_to: [tests/automations/, .github/workflows/ci.yaml, memory/equivalent-mutants.md]
  checked: 2026-11-08
---

Decided 2026-11-08 when milestone M2 was closed.

- **Where they come from.** Each reference automation in `tests/automations/` is derived from a real automation of the maintainer: same structure and logic, neutral names (no real names, entities or places), English texts. The real file is never copied into the repository. Tests that use real entity names stay outside it.
- **Floor, not 90 %.** The CI floor of each fixture is the mutation score measured when it was written, **rounded down** (44 of 45 is 97.8 %, so the floor is 97). A common 90 % does not fit, because an equivalent mutant counts as a survivor (`sun_shutter` has 22 of 25, 88 %, and all three survivors are equivalent). The floors are in the matrix of `.github/workflows/ci.yaml`. A new fixture adds its entry; a lower score means a test got weaker.
- **Every survivor is judged** and, if equivalent, recorded in `memory/equivalent-mutants.md` with the reason, before the floor is set.
- **Rounded percentages fail.** The first floors were taken from the printed, rounded percentage and failed two fixtures; compute `killed / (killed + survived)` yourself.

**Constructs without a fixture** (add one when a real case needs it): `zone` and `event_data` triggers (the maintainer's automations use neither), `parallel`, a `time` trigger with an `input_datetime`, `sun` and `calendar` triggers, `webhook`, and device triggers (they do not load at all, see `docs/writing-tests.md`).

**How to apply:** before adding a fixture, name the construct or the defect it shows that no fixture shows yet. Each fixture costs CI minutes (about 3 s per mutant, 8 runs side by side take about 2 minutes).
