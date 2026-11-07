---
name: open
description: What is not done yet, and what each open item waits for.
metadata:
  type: status
  applies_to: [ROADMAP.md, SECURITY.md, RELEASING.md, pyproject.toml, roadmap/M1-repository-and-first-ci.md]
  updated: 2026-11-07
---

Delete an item when it is done. An item the size of a milestone belongs in `ROADMAP.md`; the log in `roadmap/log/` records it when it lands.

- **Create the repository, make the first commit, run CI once, release 0.1.0** ([M1](roadmap/M1-repository-and-first-ci.md)). Waits for the maintainer's go-ahead (remote, tag, publishing).
- **Before the first public push:** enable GitHub private vulnerability reporting (`SECURITY.md` names it), add the repository URLs to `pyproject.toml`, and update the sentences in the README and in `ROADMAP.md` that say there is no remote or that CI has not run.
- **Broaden the reference set** ([M2](roadmap/M2-broaden-reference-set.md)). Can start now.
- **The name.** Decide at the latest at milestone M5; see `memory/name-and-package.md`.
- **The rest** is in `ROADMAP.md`.
