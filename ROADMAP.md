# ha-blueprint-test-harness roadmap

**Stage: release 0.3.0 is out** · next: a compatibility layer so that new Home Assistant versions touch one place (M3), then release 0.4.0

> **Last reviewed:** 2026-11-08 · **Last updated:** 2026-11-08 · **Change:** M2 (reference set) and M6 (direct automations) done, unreleased; release 0.4.0 waits

## Direction

**Now:** a testing harness that runs Home Assistant automation blueprints as they are, against simulated states, events and time, and that measures whether the tests would notice a broken blueprint (mutation testing).

**Next:** the other kinds of blueprints (script, template), then automations, scripts and helpers that are written directly instead of from a blueprint.

**In the long run:** one testing harness for everything that people build for Home Assistant, including integrations. The purpose is stable, safe development, and that includes development done with the help of AI agents: results are deterministic and machine-readable, a green run says something because the tests themselves are measured, and nothing needs a real device or a real instance. Larger thinking that is not ready to become work, and ideas from users, are collected in [`VISION.md`](VISION.md).

Two things have to hold the whole way, and the milestones below are ordered around them:

1. **Modular.** The core (simulated states, time, recorded services, mutation) is independent of the kind of thing under test. Each kind (blueprint, automation, script, helper, integration) is a small adapter on top of it.
2. **Easy to move to a new Home Assistant version.** Home Assistant ships a release every month and patch releases in between (the pinned test package for 2026.10.4 shows four patch releases in October). The harness must not need rewriting each time, and it must be able to test against several versions at once.

## Status (2026-11-08)

### Working today

- `BlueprintEnv`: load a blueprint with `use_blueprint`, set initial states, mock any service, set up real components (for example `sun`), freeze and advance the clock, set states, fire events, read the recorded calls.
- Mutation tool: structural changes (drop an item, drop `from`/`to`/`for`/..., swap `from` and `to`, swap `turn_on`/`turn_off`, mode, delays, booleans, input defaults) and text changes inside Jinja templates (comparisons, `and`/`or`, `not`, `true`/`false`). Outcomes killed, survived, invalid, error; a score; `--fail-under`.
- Runs on the core test package `pytest-homeassistant` and, for older Home Assistant versions, on `pytest-homeassistant-custom-component` (since 0.2.0).
- Two reference blueprints: Home Assistant's own `motion_light.yaml` and a small original fixture for time patterns and sun conditions.
- CI on every push and pull request (tests and mutation runs on Linux), and a release workflow that built and published 0.1.0, 0.2.0 and 0.3.0 (it can also be started by hand as a dry run).

### Not yet

- Automation blueprints only.
- One Home Assistant version at a time, and the harness uses Home Assistant internals directly, in several places.
- No branch coverage. Not on PyPI; the wheel is attached to the GitHub release.
- Few reference blueprints so far, and only the trigger kinds state, time pattern and sun. Numbers: `status/numbers.md`.

## Milestones

The state of a milestone lives only in this table: `open`, `active`, `done`, `idea` or `direction`. A milestone with content has a file in `roadmap/`; a finished one has none (what is still true afterwards goes to `memory/` or the README).

| ID | Milestone | State | Detail |
| --- | --- | --- | --- |
| M0 | Prototype: environment, mutation tool, CI file | done | — |
| M1 | Repository, first green CI run on Linux, first release (0.1.0) | done | — |
| M2 | **Broader reference set.** Six reference automations under `tests/automations/`, derived from real ones, each with tests and a mutation floor in CI (8 runs with the two blueprints, side by side); rules in `memory/reference-set-rules.md` | done | — |
| M3 | **Compatibility layer.** Every Home Assistant internal the harness uses sits behind one module, with canary tests that name what changed in a new version | open | [M3](roadmap/M3-compatibility-layer.md) |
| M4 | **Several Home Assistant generations.** A CI matrix over the blueprint's `min_version`, recent monthly releases and the current one; version markers; a weekly pin proposal | open | [M4](roadmap/M4-several-ha-generations.md) |
| M11 | **Templates and traces.** Render a template against the simulated states, read the trace of the last run (evaluated variables, the path through `choose`) and provide config entries, so that the template checks done by hand in an instance can be done in tests. Found on a real blueprint | done | — |
| M5 | **More kinds of blueprints.** Script blueprints and template (entity) blueprints, with the same fixtures-and-mutation approach | open | — |
| M6 | **Direct automations.** Load an automation written directly (no blueprint header) with `start_automation()`, mock services that return a response with `responses=`, and run the mutation tool on it (`--pick` for a list) | done | — |
| M7 | Branch coverage from Home Assistant's automation traces (which `choose` branches and conditions ran); builds on M11 | idea | — |
| M8 | Real service schemas for core domains (load the real `light`, `notify`, ... instead of a recorder), so that a changed parameter is noticed | idea | — |
| M9 | Distribution beyond the first release: a machine-readable report (JSON), a reusable GitHub Action for other repositories, publishing to PyPI | idea | — |
| M10 | Integrations and other extensions: config flows, coordinators, entities. Builds on `pytest-homeassistant`; adds the parts it lacks (for example mutation testing of Python code, scenario helpers) | direction | — |
| M12 | **Direct scripts and helpers.** The same scenarios against a script defined directly, and against helpers (template sensors, groups, input helpers); the mutation tool on those configurations. Split off from M6 | idea | — |

M3 comes before M4 on purpose: a matrix over several versions is only worth running when a version change breaks one known place. M11 stands before M5 on purpose: it answers a need found on a real blueprint, and M7 (branch coverage) builds on its trace access. The ID is M11 because IDs are never renumbered.

## Ideas, not scheduled

- A read-only differential run: the same scenario evaluated on the local engine and, through an MCP server, on a real instance, to find where they differ. The instance side is read-only; it needs a harmless sink instead of the real service and explicit approval before any write.
- Mutations inside templates for numbers and filters; mutations in `choose` branch bodies.
- Front-end extensions (custom cards, dashboards) need a browser and are not covered by the current approach. Whether they belong here is not decided.

## Non-goals

- Replacing `pytest-homeassistant` or `pytest-homeassistant-custom-component`. This project builds on them.
- Proving anything about real devices, or about the behaviour of an integration behind a mocked service.
- Depending on an AI agent. Humans and CI use the harness the same way.

## Open questions

- **Name.** `ha-blueprint-test-harness` fits today's scope. Once automations, helpers and integrations are in, "blueprint" is too narrow. The rename is cheap before a first release and costly after one, so decide at M5 at the latest.

## Numbers

Test counts, mutation scores and versions, with date and command: [`status/numbers.md`](status/numbers.md).

## Progress log

What happened, one dated line per larger piece of work, newest first: [`roadmap/log/2026-11.md`](roadmap/log/2026-11.md) (current month).
