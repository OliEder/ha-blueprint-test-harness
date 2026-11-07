"""Documentation example: Home Assistant logs a problem of an automation and carries on, so a test can pass while the
blueprint is broken. These tests read the log, and show how to make something happen while a service call runs."""

import pathlib

from ha_blueprint_test_harness import sets_state

BLUEPRINT = pathlib.Path(__file__).parent / "button_light.yaml"
LIGHT = "light.desk"


# The warnings and errors that Home Assistant logged for automations during the test itself. Only the "call" phase
# counts: in the teardown of a fixture `caplog.records` is empty, `caplog.get_records("call")` is not.
def problems(caplog):
    return [record.getMessage() for record in caplog.get_records("call")
            if record.name.startswith("homeassistant.components.automation")
            and record.levelname in ("WARNING", "ERROR", "CRITICAL")]


async def test_a_forgotten_service_shows_up_only_in_the_log(blueprint_env, caplog):
    # The light is on, so the press calls light.turn_off, which was not listed in services=. The test does not
    # fail by itself: nothing is recorded and the log says what went wrong.
    await blueprint_env.start(BLUEPRINT, {"light": LIGHT}, states={LIGHT: "on"}, services=["light.turn_on"])
    await blueprint_env.fire_event("button_pressed")
    assert blueprint_env.calls == []
    assert any("Service not found" in message for message in problems(caplog))


async def test_a_complete_setup_logs_no_problem(blueprint_env, caplog):
    # Both services are listed, so the press works and the log has no warning or error.
    await blueprint_env.start(BLUEPRINT, {"light": LIGHT}, states={LIGHT: "on"}, services=["light.turn_on", "light.turn_off"])
    await blueprint_env.fire_event("button_pressed")
    assert [call.name for call in blueprint_env.calls] == ["light.turn_off"]
    assert problems(caplog) == []


async def test_something_can_happen_while_a_service_call_is_running(blueprint_env):
    # An effect runs inside the mocked service call, so it can change a state at exactly that moment, here: another
    # press arrives while the light is being switched. This is how races are tested. The press inside the call is
    # a second event for the blueprint, which toggles the light on again.
    fired = []

    async def switch_off_and_press_again(hass, call):
        hass.states.async_set(LIGHT, "off")
        if not fired:
            fired.append(True)
            hass.bus.async_fire("button_pressed")

    await blueprint_env.start(BLUEPRINT, {"light": LIGHT}, states={LIGHT: "on"},
                              services=["light.turn_on", "light.turn_off"],
                              effects={"light.turn_off": switch_off_and_press_again, "light.turn_on": sets_state("on")})
    await blueprint_env.fire_event("button_pressed")
    await blueprint_env.settle()
    assert [call.name for call in blueprint_env.calls] == ["light.turn_off", "light.turn_on"]
