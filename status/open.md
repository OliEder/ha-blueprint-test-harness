---
name: open
description: What is not done yet, and what each open item waits for.
metadata:
  type: status
  applies_to: [ROADMAP.md, RELEASING.md, roadmap/M1-repository-and-first-ci.md, roadmap/M2-broaden-reference-set.md]
  updated: 2026-11-07
---

Delete an item when it is done. An item the size of a milestone belongs in `ROADMAP.md`; the log in `roadmap/log/` records it when it lands.

- **Release 0.1.0** ([M1](roadmap/M1-repository-and-first-ci.md)) by the steps in `RELEASING.md`. Steps 1 to 5 are done on the local branch `release/0.1.0` (commit `Release 0.1.0`, not pushed): version set, changelog dated, `numbers.md` updated, 168 tests pass, wheel and archive build and pass `twine check`, the wheel installs into a fresh environment. Left: push the branch, pull request, merge (maintainer), tag `v0.1.0` (maintainer), first run of the release workflow (never run, may fail), review and publish the draft, then steps 8 and the development version after the release. Waits for the maintainer's go-ahead.
- **PyPI** (milestone M9). Decide the name first: a name on PyPI cannot be taken back, and `memory/name-and-package.md` says to reconsider it by M5. Then register a pending trusted publisher in the account's Publishing settings on pypi.org (GitHub Actions, this repository, workflow file, optional environment) and add a publish job to `release.yaml`. A pending publisher does not reserve the name. The permissions and the action version for the job were not looked up; check PyPI's trusted-publishing guide when you get there.
- **Making the project known.** After the first release: answer the two forum feature requests, propose it to an awesome list, add `good first issue` issues and `CONTRIBUTING.md`. Details and rules: `memory/adoption-and-outreach.md`.
- **Broaden the reference set** ([M2](roadmap/M2-broaden-reference-set.md)). Can start now.
- **The name.** Decide at the latest at milestone M5; see `memory/name-and-package.md`.
- **The rest** is in `ROADMAP.md`.
