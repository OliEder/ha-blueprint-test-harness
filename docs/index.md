# Documentation

`ha-blueprint-test-harness` runs a Home Assistant **automation blueprint** inside a throw-away Home Assistant, lets you set states, fire events and move a clock, and records which services the blueprint called. A second tool breaks the blueprint in small ways to check that your tests would notice.

Read in this order:

| You want to | Read |
| --- | --- |
| Install it and run a first test | [Getting started](getting-started.md) |
| Set it up in your own project, locally and in CI | [Configuring your project](configuring-your-project.md) |
| Write tests: the API, the common patterns, what is simulated | [Writing tests](writing-tests.md) |
| Find out whether your tests are any good | [Mutation testing](mutation-testing.md) |
| Fix an error message | [Troubleshooting](troubleshooting.md) |

The overview, the credits and the licence are in the [README](../README.md). Versions and the public API are in [`RELEASING.md`](../RELEASING.md), changes per version in [`CHANGELOG.md`](../CHANGELOG.md).

## What it is, and what it is not

- It tests **blueprint logic**: triggers, conditions, templates, waits, delays and which services get called with which data.
- It does **not** talk to a real Home Assistant instance or a device. Every service you list in `services=` is replaced by a recorder that accepts any data, so a parameter that a real integration would reject goes unnoticed.
- It supports **automation blueprints only**. Script and template blueprints are not implemented.
- It is **not an official Home Assistant project.** It is built on `pytest-homeassistant` (or the older `pytest-homeassistant-custom-component`), which use internals of Home Assistant; those can change between versions.

## State of these pages

Written and checked on 2026-11-07 with Home Assistant 2026.10.4, `pytest-homeassistant-custom-component` 0.13.375 and Python 3.14, on macOS; the support for `pytest-homeassistant` 2026.11.0 (Home Assistant 2026.11.0) was added and run on 2026-11-08. The runnable examples are in [`examples/`](examples/) and are run by the project's own test suite, so they cannot drift from the code unnoticed. Steps that were not run are marked "not tried".
