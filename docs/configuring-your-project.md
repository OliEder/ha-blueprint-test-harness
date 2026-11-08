# Configuring your project

How to set the harness up so that it works for you and for everybody else who clones your repository, locally and in CI. For the first install see [Getting started](getting-started.md).

## A layout that works

```text
my-blueprints/
  blueprints/
    automation/
      my_blueprint.yaml        the blueprint you publish
  tests/
    test_my_blueprint.py       your tests
  conftest.py                  loads the harness
  pytest.ini                   asyncio mode
  requirements-dev.txt         pinned test dependencies
```

Nothing forces this layout. The only rule is that the path you give to `start()` points at a real blueprint file.

## The two files that must exist

`pytest.ini`

```ini
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
addopts = -p no:respx
testpaths = tests
```

`asyncio_mode = auto` lets you write `async def test_...` without a decorator. Without it every test errors before it runs. `-p no:respx` is needed with `pytest-homeassistant`, which fails at startup otherwise; with the older package it does no harm.

`conftest.py`

```python
import pytest

# Makes pytest load the harness' fixture (`blueprint_env`) for every test in this project.
pytest_plugins = ["ha_blueprint_test_harness.pytest_plugin"]


# Home Assistant's test setup fails a test that ends with timers still armed. Some blueprints leave timers
# armed (a time_pattern trigger does), so tell it that this is expected.
@pytest.fixture
def expected_lingering_timers() -> bool:
    return True
```

The fixture `expected_lingering_timers` is only needed for blueprints that leave timers armed, for example with a `time_pattern` trigger (see [Troubleshooting](troubleshooting.md)); it does no harm for the others.

If you already have a `conftest.py`, add the two parts to it. The plugin must be named in `pytest_plugins` there: passing `-p ha_blueprint_test_harness.pytest_plugin` on the command line does not work.

## Point `start()` at your blueprint

`start()` takes the path to the blueprint file. A path relative to the test file is the most robust:

```python
import pathlib

# The blueprint next to the tests folder, found whatever directory pytest is started from.
BLUEPRINT = pathlib.Path(__file__).parent.parent / "blueprints" / "automation" / "my_blueprint.yaml"
```

The blueprint can be one of your own, one you downloaded, or one that ships with Home Assistant (as in [Getting started](getting-started.md#4-your-first-test)). `start()` copies the file into a temporary configuration folder; your file is never changed. Inputs you pass are checked by Home Assistant against the blueprint: a missing required input or a blueprint that does not load raises `BlueprintLoadError`.

## Pin the versions

Home Assistant releases every month and the test package follows it. The harness does not install a test package (there are two, and a pin of yours must not clash), so you choose and pin it. For repeatable runs put the combination you tested in `requirements-dev.txt`:

```text
ha-blueprint-test-harness @ https://github.com/OliEder/ha-blueprint-test-harness/releases/download/v0.4.0/ha_blueprint_test_harness-0.4.0-py3-none-any.whl#sha256=<hash>
pytest-homeassistant==2026.11.0
```

Take `<hash>` from the file `SHA256SUMS` in the release (from 0.4.0 on; the line for the wheel). pip then refuses a file that differs. To pin every package, not only these two, compile a lock file with hashes and install it with `--require-hashes`: `uv pip compile requirements-dev.txt --generate-hashes -o requirements-dev.lock`, then `python -m pip install --require-hashes -r requirements-dev.lock` (this project does the same).

`2026.11.0` is the version of `pytest-homeassistant` this harness was tested with (Home Assistant 2026.11.0, Python 3.14.2 or newer). The older `pytest-homeassistant-custom-component==0.13.375` (Home Assistant 2026.10.4) was tested as well; use one of the two, never both. The wheel URL above is the release asset of the version in it; for another version change the version and the hash. To follow a state of the repository use the `git+https://...` source from [Getting started](getting-started.md#2-install) with a tag or a commit (`@v0.4.0`).

When you move to a newer test package, run your tests and the mutation tool again. The harness uses Home Assistant internals in several places, so a new Home Assistant version can break it; if it does, [open an issue](https://github.com/OliEder/ha-blueprint-test-harness/issues).

## Real components

By default only the `automation` component is set up for real. A blueprint that needs more (the most common case is `sun`, for sunrise and sunset conditions) lists them:

```python
await blueprint_env.start(BLUEPRINT, inputs, components=["sun"], ...)
```

`components` accepts Home Assistant core integrations that can be set up with an empty configuration. Custom integrations are not loaded: not tried.

## Run it in GitHub Actions

A workflow for your repository, adapted from this project's own `ci.yaml` (which runs on every push). The adapted file itself was **not run in a third-party repository**; its commands were run locally in a fresh environment.

```yaml
name: Blueprint tests

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7   # better: the commit id of a version, with the version as a comment
        with:
          persist-credentials: false
      - uses: actions/setup-python@v7
        with:
          python-version: "3.14"
          cache: pip
          cache-dependency-path: requirements-dev.lock
      - run: python -m pip install --require-hashes -r requirements-dev.lock
      - run: python -m pytest -q -p no:cacheprovider
      # Optional: fail when the tests stop noticing broken blueprints. See "Mutation testing".
      - run: >
          python -m ha_blueprint_test_harness.mutate blueprints/automation/my_blueprint.yaml
          --fail-under 100 -- python -m pytest -q -x -p no:cacheprovider tests/test_my_blueprint.py
```

Notes:

- Use `pull_request`, not `pull_request_target`, and no secrets: a pull request from a fork runs its own test code in the job.
- Choose `--fail-under` to fit your blueprint. 100 is a good goal and a demanding start; a survivor that changes nothing real (an "equivalent" change) is explained in [Mutation testing](mutation-testing.md#reading-a-survivor).
- `persist-credentials: false` keeps the token out of `.git/config`, where test code of a pull request could read it.
- A tag such as `@v7` can be moved by whoever controls the action. Pin to the commit id (`actions/checkout@<40 characters> # v7.0.1`) and let Dependabot propose updates (`package-ecosystem: github-actions`); this project does so. The versions in the snippet move on: check the current ones when you copy it.

## Keep untrusted blueprints away from secrets

Running tests runs Python, and loading a blueprint runs its templates in Home Assistant's template sandbox. Home Assistant also reads the blueprint file with its own YAML loader, where `!env_var` and `!include` read environment variables and files outside the sandbox; the harness refuses such a blueprint since 0.4.0 (`start()` raises `BlueprintLoadError`), earlier versions do not. Do not run blueprints or tests from people you do not trust with secrets in the environment or outside a throw-away environment. See [`SECURITY.md`](../SECURITY.md).
