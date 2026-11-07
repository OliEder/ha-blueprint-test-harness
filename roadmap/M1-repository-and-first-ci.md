---
id: M1
title: Repository, first green CI run on Linux, first release
description: The repository and the first green CI run on Linux exist; what is left is the first release, 0.1.0.
metadata:
  type: roadmap-item
  depends_on: []
  applies_to: [.github/workflows/release.yaml, RELEASING.md, CHANGELOG.md, status/open.md]
  updated: 2026-11-07
---

**Goal.** Version 0.1.0 is released by the process in `RELEASING.md`.

**Done so far** (2026-11-07): the repository is public, the licence is Apache-2.0, the first CI run on Linux was green (`tests` and `mutation`), private vulnerability reporting is on, and `main` is protected.

**Scope**
- Follow `RELEASING.md` for 0.1.0, including the first run of `.github/workflows/release.yaml`. Fix what that first run shows.

**Done when**
- `v0.1.0` exists as a GitHub release with the built files attached.
- The supported-versions line in `SECURITY.md` names the released version, and `status/numbers.md` records the release workflow's first run.

**Waits for.** The maintainer's go-ahead to tag and to publish.
