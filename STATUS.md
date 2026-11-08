# Status

A short index. Where things are, which files a task needs, and where the current numbers, open items and commands live. Read the map, then open only what your task needs. Last updated 2026-11-08.

## Right now

- Pre-1.0 for automation blueprints. The repository is public and CI on GitHub is green. Release 0.4.1 is published (a fix of 0.4.0: the mutation tool accepts YAML aliases again); release 0.4.0 (automations written directly with `start_automation()`, `responses=`, the mutation tool on automations and `--jobs`, and the fixes of a security audit; 0.3.0 added `render()`, `last_trace()` and config entries, 0.2.0 support for `pytest-homeassistant`). The development version is 0.5.0.dev0.
- Next: a repository and a first CI run, then a broader set of reference blueprints, then the compatibility layer (milestones in [`ROADMAP.md`](ROADMAP.md)).
- Numbers are in `status/numbers.md`, with date and command. They are not repeated here.

## Project map by task

Read the first column's files, then the rest only if needed.

| Task | Read first | If needed | Not needed |
| --- | --- | --- | --- |
| Understand or change the environment | `ha_blueprint_test_harness/env.py` | `docs/writing-tests.md`; `memory/settle-instead-of-block-till-done.md` | `mutate.py` |
| Write tests for a blueprint | `docs/writing-tests.md`, `docs/examples/` (the models) | `env.py` `start()` | `test_mutate.py`, `mutate.py` |
| Judge mutation survivors | `docs/mutation-testing.md`, `mutate.py` header | `memory/equivalent-mutants.md`, `memory/mutation-outcomes-killed-invalid.md` | `env.py` |
| Add or change a mutation operator | `mutate.py` (`_walk`, `_dict_sites`, `_template_variants`), `tests/test_mutate.py` | `docs/mutation-testing.md` (the operator table) | `env.py` |
| CI, locked versions | `.github/workflows/ci.yaml`, `requirements-*.txt` (what is wanted) | `.github/dependabot.yml`, `RELEASING.md` ("Locked versions") | the `requirements-*.lock` files: thousands of hash lines, regenerate them instead of reading |
| Install, set up or use the tool; fix an error message | `docs/index.md`, then the page it names | `README.md` | `mutate.py`, `env.py` |
| Version, release or changelog | `RELEASING.md`, `CHANGELOG.md` | `pyproject.toml`, `.github/workflows/release.yaml` | |
| Security question or audit finding | `SECURITY.md`, `tests/test_security.py` | `roadmap/log/2026-11.md` (the audit entry) | |
| Work on a milestone | `ROADMAP.md` (the table), then the milestone's file in `roadmap/` | the `memory/` entries it names; `roadmap/log/` for the recent past | the other milestone files |
| Current numbers, open items, commands | the matching file in `status/` | | the other `status/` files |
| Find a fact or a past decision | `MEMORY.md` (the index; open only the entries that match) | the entries in `memory/` | the rest of `memory/` |
| Naming, scope, "why not X" | `MEMORY.md`, `ROADMAP.md` | | |
| Long-term direction, ideas, community input | `VISION.md` | `ROADMAP.md` | |
| How to write and update these documents | `AGENTS.md`, section "Keeping the documents current" | | |
| Security questions | `SECURITY.md` | | |

No file is large. Longest: `mutate.py` (about 420 lines), `env.py` (about 200).

## Status files

Decisions are not listed here: they are the rules in `AGENTS.md` and the entries of type decision in `memory/`.

- [Numbers](status/numbers.md): read when you need a test count, a mutation score, a version or the CI state, or before you quote one.
- [Open items](status/open.md): read when you pick the next piece of work or wonder what something waits for.
- [Practical](status/practical.md): read when a command, the set-up or a local quirk (editor, shell) is the question.
