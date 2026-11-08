---
name: open
description: What is not done yet, and what each open item waits for.
metadata:
  type: status
  applies_to: [ROADMAP.md, RELEASING.md]
  updated: 2026-11-08
---

Delete an item when it is done. An item the size of a milestone belongs in `ROADMAP.md`; the log in `roadmap/log/` records it when it lands.

- **PyPI** (milestone M9). Not part of releases 0.1.0 to 0.3.0, which are GitHub releases only. The name must be settled first (see "The name"). Then register a pending trusted publisher in the account's Publishing settings on pypi.org (GitHub Actions, this repository, workflow file, optional environment) and add a publish job to `release.yaml`. A pending publisher does not reserve the name. The permissions and the action version for the job were not looked up; check PyPI's trusted-publishing guide when you get there.
- **Making the project known.** After the first release: answer the two forum feature requests, propose it to an awesome list, add `good first issue` issues and `CONTRIBUTING.md`. Details and rules: `memory/adoption-and-outreach.md`.
- **Release 0.4.0.** Pull requests 11 (M6) and 12 (M2, `--jobs`, the CI matrix) are open, 12 on top of 11; merge them first. Contents of 0.4.0: `start_automation()`, `responses=`, the mutation tool on automations and `--jobs`, six reference automations. `main` carries 0.3.0 until 11 is merged (the branch has `0.4.0.dev0`). Steps: `RELEASING.md`.
- **The name.** Open; the maintainer decides. Rules that hold for every choice: it must be settled before any PyPI publication, and reconsidered at the latest at milestone M5. The GitHub release 0.1.0 does not claim a PyPI name, but it publishes the import name `ha_blueprint_test_harness`; a later rename changes that name for its users (a breaking change, allowed before 1.0, which raises the MINOR number). Details and the availability check: `memory/name-and-package.md`.
- **The rest** is in `ROADMAP.md`.
