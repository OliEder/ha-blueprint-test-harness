---
name: name-and-package
description: Why the project is called ha-blueprint-test-harness, which names were free on 2026-11-07, and when to reconsider the name.
metadata:
  type: decision
  applies_to: [README.md, ROADMAP.md]
  checked: 2026-11-07
---

Chosen 2026-11-07: project `ha-blueprint-test-harness`, Python package `ha_blueprint_test_harness`. "ha" ties it to Home Assistant, "blueprint" is today's scope, "test" says what it is. It is not an official Home Assistant project; the name Home Assistant belongs to its foundation.

Free on PyPI that day (HTTP 404): `ha-blueprint-test-harness`, `ha-blueprint-testing-harness`, `ha-blueprint-testing`, `ha-testing-harness`, `ha-dev-harness`. A GitHub search for the chosen name found no similar repository.

**Why:** "blueprint" becomes too narrow once automations, helpers and integrations are covered (see the roadmap).

**How to apply:** decide on a rename at the latest at milestone M5 and before a first release, when it is still cheap. Check PyPI and GitHub again then; the list above is a dated snapshot.
