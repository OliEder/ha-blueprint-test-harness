---
name: scope-and-version-compatibility
description: Decided scope (blueprints, then automations, scripts, helpers, in the long run all extensions) and why version handling is designed in early.
metadata:
  type: decision
  applies_to: [ROADMAP.md]
  checked: 2026-11-07
---

Decided 2026-11-07. The tool starts with automation blueprints, then covers other blueprint kinds, then automations, scripts and helpers written directly, and in the long run all kinds of extensions including integrations. The aim is stable, safe development, including development with AI agents: deterministic, machine-readable results and tests that are themselves measured. "test" is in the name because it is a testing tool; the name stays open for other tools to be built around it.

**Why:** Home Assistant releases monthly with patch releases in between (2026.10.4 is the fourth patch release of October's release), so the project must move to new versions easily and test on several at once. Version handling is designed in (milestones M3 and M4), not added later.

**How to apply:** put anything that touches a Home Assistant internal behind the compatibility module once it exists (M3); do not spread new direct imports through the code. Revisit the name before the scope goes beyond blueprints (M5).
