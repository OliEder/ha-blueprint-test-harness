---
name: first-release-lessons
description: What the first release, 0.1.0, taught about tagging, the protected tags and the dry run.
metadata:
  type: pitfall
  applies_to: [RELEASING.md, .github/workflows/release.yaml]
  checked: 2026-11-07
---

- **Tag with git, do not create a release in the web interface.** 0.1.0 ended up with two releases for one tag: one published by hand without files and with generated notes, and the workflow's draft (with an "untagged" address). It was cleaned up by deleting the empty release and publishing the draft; the tag was not touched.
- **A failed tag run cannot be repaired.** The release tags are protected (no update, no deletion), and a re-run reads the workflow from the tagged commit, so a fix to the workflow needs a new tag (0.1.1). That is why the workflow can be started by hand as a dry run on `main` before the tag. The dry run covers everything except the last step (`gh release create`); that step worked on the real tag.
- **After publishing, check it as a stranger would:** the documented wheel URL answers without login, the checksums equal those of the draft's files, and the documented requirement line installs the version into a fresh environment.

**Why:** these three cost time or could not be undone cheaply; the first release was the first run of the workflow.

**How to apply:** read before the next release and follow `RELEASING.md` steps 5 to 8. Check the action versions in `.github/workflows/` first; they were bumped untested for the artifact steps and only the dry run proved them.
