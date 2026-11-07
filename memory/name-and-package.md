---
name: name-and-package
description: Why the project is called ha-blueprint-test-harness, which names were free on 2026-11-07, and when to reconsider the name.
metadata:
  type: decision
  applies_to: [README.md, ROADMAP.md]
  checked: 2026-11-07
---

Chosen 2026-11-07: project `ha-blueprint-test-harness`, Python package `ha_blueprint_test_harness`. "ha" ties it to Home Assistant, "blueprint" is today's scope, "test" says what it is. It is not an official Home Assistant project; the name Home Assistant belongs to its foundation.

Free on PyPI that day (HTTP 404): `ha-blueprint-test-harness`, `ha-blueprint-testing-harness`, `ha-blueprint-testing`, `ha-testing-harness`, `ha-dev-harness`. Checked again on 2026-11-07 (also 404): `ha-blueprint-test-harness`, `ha-blueprint-testing`, `ha-testing-harness`, `ha-blueprint-testkit`, `ha-test-harness`, `hass-test-harness`, `ha-automation-test-harness`. A GitHub search for the chosen name found no similar repository.

**Why:** "blueprint" becomes too narrow once automations, helpers and integrations are covered (see the roadmap).

**How to apply:** the name is open until the maintainer decides. Three rules hold for every choice. (1) Settle the name before any PyPI publication. (2) Reconsider it at the latest at milestone M5. (3) The GitHub release 0.1.0 claims no PyPI name but publishes the import name `ha_blueprint_test_harness`; renaming later changes it for users, which is a breaking change (allowed before 1.0, it raises the MINOR number; see `RELEASING.md`). Check PyPI and GitHub again when you decide; the lists above are dated snapshots. Two options were weighed on 2026-11-07: keep the name and publish only on GitHub first, or choose a broader name now that matches the long-term scope; no choice has been recorded.
