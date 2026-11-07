---
name: practical
description: Set-up and the commands used most.
metadata:
  type: status
  applies_to: [requirements-dev.txt, pytest.ini, .github/workflows/ci.yaml]
  updated: 2026-11-07
---

- Set-up: `uv venv --python 3.14 .venv && uv pip install --python .venv/bin/python -r requirements-dev.txt`
- Tests: `.venv/bin/python -m pytest -q`
- Mutation tool: `.venv/bin/python -m ha_blueprint_test_harness.mutate <blueprint.yaml> [--timeout S] [--fail-under PCT] -- <test command>`
- Changes to `main` go through a pull request; only the maintainer may push to it directly.
- Build the package: `uv build --out-dir <folder>`
- CI steps run under `bash`. To try a step locally, put it in a file and run `bash -e file.sh`.
- An editor reports unresolved imports unless it uses `.venv` as its interpreter.
