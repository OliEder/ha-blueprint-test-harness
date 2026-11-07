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
testpaths = tests
```

`asyncio_mode = auto` lets you write `async def test_...` without a decorator. Without it every test errors before it runs.

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

Home Assistant releases every month and the test package follows it. The harness does not pin the test package (so that it does not clash with a pin of yours), which means a fresh install gets the newest one. For repeatable runs put the combination you tested in `requirements-dev.txt`:

```text
ha-blueprint-test-harness @ https://github.com/OliEder/ha-blueprint-test-harness/releases/download/v0.1.0/ha_blueprint_test_harness-0.1.0-py3-none-any.whl
pytest-homeassistant-custom-component==0.13.375
```

`0.13.375` is the version this harness was tested with (Home Assistant 2026.10.4). The wheel URL above is the release asset of 0.1.0 (published on 2026-11-07; the line was checked to install it into a fresh environment). For a newer version change the version in the URL. To follow the main branch use the `git+https://...` source from [Getting started](getting-started.md#2-install).

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
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.14"
          cache: pip
          cache-dependency-path: requirements-dev.txt
      - run: python -m pip install -r requirements-dev.txt
      - run: python -m pytest -q -p no:cacheprovider
      # Optional: fail when the tests stop noticing broken blueprints. See "Mutation testing".
      - run: >
          python -m ha_blueprint_test_harness.mutate blueprints/automation/my_blueprint.yaml
          --fail-under 100 -- python -m pytest -q -x -p no:cacheprovider tests/test_my_blueprint.py
```

Notes:

- Use `pull_request`, not `pull_request_target`, and no secrets: a pull request from a fork runs its own test code in the job.
- Choose `--fail-under` to fit your blueprint. 100 is a good goal and a demanding start; a survivor that changes nothing real (an "equivalent" change) is explained in [Mutation testing](mutation-testing.md#reading-a-survivor).
- Versions of `actions/checkout` and `actions/setup-python` move on; check the current major versions when you copy this.

## Keep untrusted blueprints away from secrets

Loading a blueprint runs its templates in Home Assistant's template sandbox, and running tests runs Python. Do not run blueprints or tests from people you do not trust with secrets in the environment. See [`SECURITY.md`](../SECURITY.md).
