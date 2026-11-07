---
id: M1
title: Repository, first green CI run on Linux, first release
description: Put the project in a repository with history, get its CI green on Linux for the first time, and make the first release.
metadata:
  type: roadmap-item
  depends_on: []
  applies_to: [.github/workflows/ci.yaml, .github/workflows/release.yaml, RELEASING.md, CHANGELOG.md, SECURITY.md, status/open.md]
  updated: 2026-11-07
---

**Goal.** The project lives in a repository with history, `tests` and `mutation` in `.github/workflows/ci.yaml` have run green on Linux, and version 0.1.0 is released by the process in `RELEASING.md`.

**Scope**
- Create the repository (visibility is the maintainer's decision), make the first commit without `.venv`, push.
- Enable GitHub private vulnerability reporting, which `SECURITY.md` names as the reporting channel.
- Add the repository URLs to `pyproject.toml`.
- Run the workflow and fix what the first Linux run shows (the Python 3.14 runner, paths).
- Follow `RELEASING.md` for 0.1.0, including the first run of `.github/workflows/release.yaml`.

**Done when**
- The `tests` and `mutation` jobs are green on `main`, and `status/numbers.md` says so, with the date.
- `ROADMAP.md` ("Not yet") and the README no longer say that there is no remote or that CI has not run, and the supported-versions line in `SECURITY.md` names the released version.
- `v0.1.0` exists as a GitHub release with the built files attached.

**Waits for.** The maintainer's go-ahead to create the remote, to tag and to publish.
