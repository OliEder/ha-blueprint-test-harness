---
id: M4
title: Several Home Assistant generations - CI matrix, version markers, pin proposals
description: Run the tests on several Home Assistant releases and make moving the pin a routine, reviewed change.
metadata:
  type: roadmap-item
  depends_on: [M1, M3]
  applies_to: [.github/workflows/ci.yaml, requirements-dev.txt, memory/scope-and-version-compatibility.md]
  updated: 2026-11-07
---

**Goal.** The harness is tested on a blueprint's `min_version`, on the last few monthly releases and on the current one. Moving to a new release is a small change that a person reviews.

Home Assistant ships a release each month with patch releases in between, so this has to be routine.

**Scope**
- **CI matrix** over the `min_version` of the blueprint under test, the last few monthly releases and the current one; the beta and the dev branch run as allowed failures.
- **Version markers in tests.** A test can say that it needs a minimum version, or that behaviour differs below one, instead of being deleted or skipped by hand.
- **A table of generations.** Which test-package release belongs to which Home Assistant release, generated from what is installed rather than kept by hand.
- **Pin policy.** The pin stays exact. A weekly job proposes the next pin and runs the matrix; a person merges.

**Open**
- How many past releases belong in the matrix, and what that costs in CI time.
- How to install a specific Home Assistant generation through the test package's release numbering.

**Done when**
- The matrix is green on at least the current and the previous release, and a failing beta does not block.
- At least one test uses a version marker.
- The weekly job produces a pin proposal that a person can merge.
