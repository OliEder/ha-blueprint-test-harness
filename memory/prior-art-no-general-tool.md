---
name: prior-art-no-general-tool
description: Earlier work this project builds on, and what was found when searching for an existing blueprint test tool on 2026-11-07 (nothing general).
metadata:
  type: research
  applies_to: [README.md]
  checked: 2026-11-07
---

The starting point was the blueprint test setup of MrCodeLabs for a go-eCharger PV blueprint (Apache-2.0): a harness that runs the blueprint's templates and actions against synthetic states in a Jinja sandbox, with scenario tests. This project took the idea and several first scenarios, not the code, and runs the blueprint in a real Home Assistant instead. The README credits him.

Searched 2026-11-07 on the web and in GitHub code. Closest others: Home Assistant core's `tests/components/automation/test_blueprint.py` and `template/test_blueprint.py` (the pattern this project follows, Apache-2.0); `ChuckBuilds/ha-blueprints` (standalone scripts that start a headless Home Assistant per project; no licence, so not reused); an open feature request for a YAML test framework on the Home Assistant community forum (since 2024-02, no answer from the team); `ha-testcontainer` (visual tests, not automation logic). The searches cannot prove absence.

**Why:** it answers "does this already exist, and who did the groundwork?" without repeating the search.

**How to apply:** keep the credit in the README current. Do not re-run the search unless the claim "no general tool exists" matters for a decision; if it does, search again and update this entry with the date.
