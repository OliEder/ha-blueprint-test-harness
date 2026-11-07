---
name: last-reported-weak-age-signal
description: Sensors that report only on change make last_reported a weak age signal; do not recommend an age limit from one sensor's cadence.
metadata:
  type: observation
  applies_to: []
  checked: 2026-11-07
---

Observed on one installation (read-only, 2026-11-07, three samples): one of four power sensors seemed to report only when its value changed (its `last_reported` always equalled its `last_changed`), and its age reached 25 s once while the other three updated every 5 s. A short age limit based on `last_reported` can therefore skip updates although nothing is broken.

**Why:** this is why a blueprint age check should say that the report time is not the measurement time. No entity names are recorded here on purpose.

**How to apply:** do not infer from one sensor's cadence that all sensors of an installation behave alike. Measure a window before recommending a limit.
