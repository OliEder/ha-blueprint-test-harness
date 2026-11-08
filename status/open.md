---
name: open
description: What is not done yet, and what each open item waits for.
metadata:
  type: status
  applies_to: [ROADMAP.md, RELEASING.md]
  updated: 2026-11-08
---

Delete an item when it is done. An item the size of a milestone belongs in `ROADMAP.md`; the log in `roadmap/log/` records it when it lands.

- **PyPI** (milestone M9). Not part of releases 0.1.0 to 0.4.1, which are GitHub releases only. The name must be settled first (see "The name"). Then register a pending trusted publisher in the account's Publishing settings on pypi.org (GitHub Actions, this repository, workflow file, optional environment) and add a publish job to `release.yaml`. A pending publisher does not reserve the name. The permissions and the action version for the job were not looked up; check PyPI's trusted-publishing guide when you get there.
- **Making the project known.** After the first release: answer the two forum feature requests, propose it to an awesome list, add `good first issue` issues and `CONTRIBUTING.md`. Details and rules: `memory/adoption-and-outreach.md`.
- **Signed provenance for releases.** 0.4.0 has a `SHA256SUMS` file but no attestation (`actions/attest-build-provenance`, needs `id-token: write` and `attestations: write` in the build job). It cannot be tried with a dry run, and a tag cannot be moved, so add it with a release candidate or accept a failed release and a PATCH version.
- **Maintainer's side of the audit.** GitHub's setting "Block command line pushes that expose my email" (40 of 54 commits in the public history carry a private address); whether to add a warning to the published 0.3.0 release (it has the issue F1 of `SECURITY.md`).
- **The name.** Open; the maintainer decides. Rules that hold for every choice: it must be settled before any PyPI publication, and reconsidered at the latest at milestone M5. The GitHub release 0.1.0 does not claim a PyPI name, but it publishes the import name `ha_blueprint_test_harness`; a later rename changes that name for its users (a breaking change, allowed before 1.0, which raises the MINOR number). Details and the availability check: `memory/name-and-package.md`.
- **The rest** is in `ROADMAP.md`.
