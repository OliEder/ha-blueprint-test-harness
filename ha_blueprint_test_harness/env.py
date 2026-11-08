"""Run a Home Assistant blueprint in-process against synthetic states, services and time.

Real: blueprint loading and input validation, templates, triggers, conditions, waits and
delays, the state machine. Not real: every service listed in ``services`` (recorded, never
executed), all integrations, all devices.

How to read this file: a test creates one ``BlueprintEnv`` (through the ``blueprint_env`` fixture),
calls ``start()`` once to load the blueprint, then pokes it with ``set_state()``, ``fire_event()`` and
``advance()`` and finally looks at ``calls`` to see which services the blueprint tried to call.
"""

from __future__ import annotations

import asyncio
import dataclasses
import datetime as dt
import inspect
import os
import pathlib
import shutil
from collections.abc import Awaitable, Callable, Iterable, Mapping
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.template import Template
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dtu

# Home Assistant's test helpers come from one of two packages: `pytest-homeassistant` (maintained in Home Assistant
# core) or `pytest-homeassistant-custom-component` (the older one). They must not be installed together, so use
# whichever is there and say what to install if neither is.
try:
    from pytest_homeassistant.common import MockConfigEntry, async_fire_time_changed
except ModuleNotFoundError:
    try:
        from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
    except ModuleNotFoundError as error:
        raise ImportError(
            "No Home Assistant test package found. Install `pytest-homeassistant` (or, for older Home Assistant "
            "versions, `pytest-homeassistant-custom-component`); see docs/getting-started.md."
        ) from error

# How many times the event loop gets to run in settle(). Home Assistant's own tests wait 10 for the same reason.
_SETTLE_ITERATIONS = 20

# A function that runs when a mocked service is called, e.g. to switch a light "on" in the simulation.
Effect = Callable[[HomeAssistant, ServiceCall], Awaitable[None] | None]


# The id the automation under test is given. Home Assistant stores no trace for an automation without an id.
_AUTOMATION_ID = "blueprint_under_test"


# What one run of the automation did, read from Home Assistant's trace. ``steps`` maps a path such as
# "action/2/choose/0/sequence/0" to what happened there; ``variables`` merges the variables every step set.
@dataclasses.dataclass(frozen=True)
class Trace:
    run_id: str
    error: str | None
    steps: Mapping[str, list[Mapping[str, Any]]]

    # The paths the run went through, in the order it reached them.
    @property
    def path(self) -> list[str]:
        return list(self.steps)

    # Every variable the run evaluated, with the value it ended up with (real types: True, 14.0, not text).
    @property
    def variables(self) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for elements in self.steps.values():
            for element in elements:
                merged.update(element.get("changed_variables") or {})
        return merged


# Raised by start() when the blueprint did not turn into a working automation (typo, missing input, ...).
# The mutation tool looks for this name in the test output to tell "broken blueprint" from "test failed".
class BlueprintLoadError(AssertionError):
    """The blueprint did not produce a working automation (invalid config, missing input, ...)."""


# One service call the blueprint made, e.g. light.turn_on with {"entity_id": ["light.hall"]}.
@dataclasses.dataclass(frozen=True)
class Call:
    """One recorded service call."""

    domain: str
    service: str
    data: Mapping[str, Any]

    # The call as "domain.service", e.g. "light.turn_on".
    @property
    def name(self) -> str:
        return f"{self.domain}.{self.service}"

    # The entities the call is aimed at, always as a set (the blueprint may pass one string or a list).
    @property
    def entity_ids(self) -> set[str]:
        """The targeted entities, whether the blueprint passed a string or a list."""
        value = self.data.get("entity_id", [])
        return {value} if isinstance(value, str) else set(value)


# Used only while the mutation tool runs: if the test asks for the blueprint that is being mutated, hand out
# the altered copy instead. Outside a mutation run this returns the path unchanged.
def _mutation_override(source: pathlib.Path) -> pathlib.Path:
    """Under ``python -m ha_blueprint_test_harness.mutate`` the blueprint being mutated is swapped for the mutant here."""
    original, mutant = os.environ.get("HA_BLUEPRINT_TEST_HARNESS_ORIGINAL"), os.environ.get("HA_BLUEPRINT_TEST_HARNESS_MUTANT")
    if original and mutant and source.resolve() == pathlib.Path(original).resolve():
        return pathlib.Path(mutant)
    return source


# Builds an Effect that sets every entity the service call is aimed at to a fixed state.
# Example: sets_state("on") for light.turn_on makes the simulated light actually turn on.
def sets_state(state: str) -> Effect:
    """Effect for a mocked service: put every targeted entity into ``state``."""

    # The function that runs on each call of the mocked service.
    def effect(hass: HomeAssistant, call: ServiceCall) -> None:
        for entity_id in Call(call.domain, call.service, call.data).entity_ids:
            hass.states.async_set(entity_id, state)

    return effect


class BlueprintEnv:
    """One blueprint-backed automation inside a throw-away Home Assistant."""

    # Stores what the test fixture hands over: the Home Assistant instance, a temporary config folder
    # and the clock freezer. Nothing is loaded yet; that happens in start().
    def __init__(self, hass: HomeAssistant, config_dir: pathlib.Path, freezer: Any) -> None:
        self.hass = hass
        self._config_dir = config_dir
        self._freezer = freezer
        self._started = False
        self.calls: list[Call] = []  # every mocked service call, in the order it happened

    # Loads the blueprint as a real automation. Steps: freeze the clock, copy the blueprint file into the
    # temporary config folder, set up real components, set initial states, mock the services, then create
    # the automation and check that it really came up. Can be called once per environment.
    async def start(
        self,
        blueprint: str | pathlib.Path,
        inputs: Mapping[str, Any] | None = None,
        *,
        states: Mapping[str, str | tuple[str, Mapping[str, Any]]] | None = None,
        services: Iterable[str] = (),
        effects: Mapping[str, Effect] | None = None,
        components: Iterable[str] = (),
        config_entries: Iterable[MockConfigEntry] = (),
        when: dt.datetime | None = None,
        alias: str = "blueprint under test",
    ) -> None:
        """Install ``blueprint``, set initial ``states`` and mock ``services``, then set up the automation.

        ``services`` are names like ``"light.turn_on"``. They are recorded in ``calls`` and
        accept any data, so a service schema that changes in the real integration is not noticed.
        ``components`` are real Home Assistant components to set up first (for example ``"sun"``
        when the blueprint uses sun conditions). ``config_entries`` are added to the system first, for template
        functions such as ``config_entry_attr``. ``when`` moves the frozen clock before anything runs.
        """
        if self._started:
            raise RuntimeError("start() can be called once per environment")
        self._started = True
        if when is not None:
            self._freezer.move_to(when)
        # Home Assistant looks for blueprints in <config>/blueprints/automation/, so put a copy there.
        self.hass.config.config_dir = str(self._config_dir)
        source = _mutation_override(pathlib.Path(blueprint))
        target = self._config_dir / "blueprints" / "automation" / "harness"
        target.mkdir(parents=True)
        shutil.copy(source, target / source.name)

        for component in components:
            assert await async_setup_component(self.hass, component, {}), component
        for entry in config_entries:
            entry.add_to_hass(self.hass)
        for entity_id, value in (states or {}).items():
            state, attributes = value if isinstance(value, tuple) else (value, None)
            self.hass.states.async_set(entity_id, state, attributes)
        for name in services:
            self._mock_service(name, (effects or {}).get(name))

        # This is the same configuration a user writes in the UI: "use this blueprint with these inputs".
        config = {"id": _AUTOMATION_ID, "alias": alias, "use_blueprint": {"path": f"harness/{source.name}", "input": dict(inputs or {})}}
        if not await async_setup_component(self.hass, "automation", {"automation": [config]}):
            raise BlueprintLoadError("the automation component did not set up")
        await self.settle()
        # Home Assistant logs a bad blueprint and carries on, so check that exactly one automation exists
        # and that it is not "unavailable".
        entity_ids = self.hass.states.async_entity_ids("automation")
        if len(entity_ids) != 1 or self.hass.states.get(entity_ids[0]).state == "unavailable":
            raise BlueprintLoadError(f"the blueprint did not produce a working automation: {entity_ids}")

    # Evaluates a template string against the simulated states, like the template tool of an instance does.
    # The result has its real type (True, 8, a list), not text.
    def render(self, template: str, variables: Mapping[str, Any] | None = None) -> Any:
        return Template(template, self.hass).async_render(dict(variables or {}))

    # The trace of the automation's last run: which variables it evaluated and which branches it took.
    # Raises LookupError when the automation has not run yet.
    def last_trace(self) -> Trace:
        return _read_last_trace(self.hass)

    # Registers a fake version of one service, e.g. "light.turn_on". Instead of doing anything real it
    # writes the call into ``self.calls`` and, if given, runs the effect (see sets_state).
    def _mock_service(self, name: str, effect: Effect | None) -> None:
        domain, service = name.split(".", 1)

        # What Home Assistant runs whenever the blueprint calls this service.
        async def handler(call: ServiceCall) -> None:
            self.calls.append(Call(call.domain, call.service, dict(call.data)))
            if effect is not None:
                result = effect(self.hass, call)
                if inspect.isawaitable(result):
                    await result

        self.hass.services.async_register(domain, service, handler)

    # Gives everything that is ready to run a chance to run, without waiting for scripts that are
    # intentionally paused (waiting for a trigger or in a delay).
    async def settle(self) -> None:
        """Let everything that is ready run.

        ``hass.async_block_till_done()`` cannot be used: a script that waits for a trigger or sits in a
        delay keeps a task open, so it would never return. Anything that needs more than
        ``_SETTLE_ITERATIONS`` loop iterations (long chains of actions) must be settled again by the test.
        """
        for _ in range(_SETTLE_ITERATIONS):
            await asyncio.sleep(0)

    # Only the calls to one service, e.g. calls_to("light.turn_off").
    def calls_to(self, name: str) -> list[Call]:
        return [call for call in self.calls if call.name == name]

    # Changes one entity's state (for example a motion sensor to "on") and lets the blueprint react.
    async def set_state(self, entity_id: str, state: str, attributes: Mapping[str, Any] | None = None) -> None:
        """Write a state and let everything it triggers run to completion."""
        self.hass.states.async_set(entity_id, state, attributes)
        await self.settle()

    # Sends an event on the Home Assistant event bus (for example a button press) and lets the blueprint react.
    async def fire_event(self, event_type: str, data: Mapping[str, Any] | None = None) -> None:
        self.hass.bus.async_fire(event_type, dict(data or {}))
        await self.settle()

    # Lets time pass without waiting: moves the frozen clock forward and runs every timer that is now due
    # (delays, "for:" durations, time_pattern triggers). Call it repeatedly for stepwise time, e.g. every 5 s.
    async def advance(self, seconds: float) -> None:
        """Move the frozen clock forward and fire every timer that is due (delays, time patterns)."""
        self._freezer.tick(dt.timedelta(seconds=seconds))
        async_fire_time_changed(self.hass, dtu.utcnow())
        await self.settle()


# The one place that reads Home Assistant's trace store. It uses internals of the `trace` component, so a new
# Home Assistant version that moves them breaks this function (and its canary test) and nothing else.
def _read_last_trace(hass: HomeAssistant) -> Trace:
    from homeassistant.components.trace.const import DATA_TRACE

    buckets = hass.data.get(DATA_TRACE, {}).get(f"automation.{_AUTOMATION_ID}")
    runs = list(buckets.runs.values()) if buckets is not None else []
    if not runs:
        raise LookupError("the automation has not run yet, so there is no trace")
    data = runs[-1].as_extended_dict()
    return Trace(run_id=data["run_id"], error=data.get("error"), steps=data["trace"])
