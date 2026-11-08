---
name: open
description: What is not done yet, and what each open item waits for.
metadata:
  type: status
  applies_to: [ROADMAP.md, RELEASING.md, roadmap/M2-broaden-reference-set.md]
  updated: 2026-11-07
---

Delete an item when it is done. An item the size of a milestone belongs in `ROADMAP.md`; the log in `roadmap/log/` records it when it lands.

- **PyPI** (milestone M9). Not part of release 0.1.0, which is a GitHub release only. The name must be settled first (see "The name"). Then register a pending trusted publisher in the account's Publishing settings on pypi.org (GitHub Actions, this repository, workflow file, optional environment) and add a publish job to `release.yaml`. A pending publisher does not reserve the name. The permissions and the action version for the job were not looked up; check PyPI's trusted-publishing guide when you get there.
- **Making the project known.** After the first release: answer the two forum feature requests, propose it to an awesome list, add `good first issue` issues and `CONTRIBUTING.md`. Details and rules: `memory/adoption-and-outreach.md`.
- **Release 0.3.0.** `render()`, `last_trace()` and `config_entries=` (M11) wait on `main` for a release; it is a MINOR version (new API before 1.0). Steps: `RELEASING.md`.
- **Broaden the reference set** ([M2](roadmap/M2-broaden-reference-set.md)). Can start now.
- **The name.** Open; the maintainer decides. Rules that hold for every choice: it must be settled before any PyPI publication, and reconsidered at the latest at milestone M5. The GitHub release 0.1.0 does not claim a PyPI name, but it publishes the import name `ha_blueprint_test_harness`; a later rename changes that name for its users (a breaking change, allowed before 1.0, which raises the MINOR number). Details and the availability check: `memory/name-and-package.md`.
- **The rest** is in `ROADMAP.md`.
