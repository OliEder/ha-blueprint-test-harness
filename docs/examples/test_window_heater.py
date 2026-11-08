"""Documentation example: tests for window_heater.yaml, a blueprint that decides in `variables` and switches in `choose`.

Shows render() (look at a template without running the blueprint), last_trace() (what the run evaluated and which
branch it took) and config_entries (template functions that need a config entry).
"""

import pathlib

from ha_blueprint_test_harness import MockConfigEntry

BLUEPRINT = pathlib.Path(__file__).parent / "window_heater.yaml"
TEMPERATURE = "sensor.room"
WINDOW = "binary_sensor.window"
HEATER = "switch.heater"
INPUTS = {"room_temperature": TEMPERATURE, "window": WINDOW, "heater": HEATER}


# Loads the blueprint with a room temperature, a window state and a heater state.
async def start(env, temperature="15", window="off", heater="off", **extra):
    await env.start(
        BLUEPRINT,
        INPUTS,
        states={TEMPERATURE: temperature, WINDOW: window, HEATER: heater},
        services=["switch.turn_on", "switch.turn_off"],
        **extra,
    )


async def test_the_run_reports_what_it_decided(blueprint_env):
    # A cold room and a closed window: the trace holds the decision as a real boolean, not as text.
    await start(blueprint_env)
    await blueprint_env.set_state(TEMPERATURE, "14")
    variables = blueprint_env.last_trace().variables
    assert variables["desired_on"] is True
    assert variables["temperature"] == 14.0


async def test_an_open_window_decides_false_as_a_boolean(blueprint_env):
    # The value that once switched a heater on with the window open: `desired_on` must be False, not the text "false".
    await start(blueprint_env, window="on")
    await blueprint_env.set_state(TEMPERATURE, "14")
    assert blueprint_env.last_trace().variables["desired_on"] is False
    assert blueprint_env.calls_to("switch.turn_on") == []


async def test_the_trace_names_the_branch_that_ran(blueprint_env):
    # Switching on is the first `choose` branch; switching off is the second. The trace path says which one ran.
    await start(blueprint_env)
    await blueprint_env.set_state(TEMPERATURE, "14")
    assert "action/2/choose/0/sequence/0" in blueprint_env.last_trace().path
    assert "action/2/choose/1/sequence/0" not in blueprint_env.last_trace().path


async def test_asking_for_a_trace_before_any_run_is_an_error(blueprint_env):
    # Nothing has triggered the automation yet, so there is no trace to read.
    await start(blueprint_env)
    try:
        blueprint_env.last_trace()
    except LookupError as error:
        assert "has not run" in str(error)
    else:
        raise AssertionError("expected a LookupError")


async def test_render_evaluates_a_template_against_the_simulated_states(blueprint_env):
    # The check done by hand in the template tool of an instance: look at a value without running the blueprint.
    await start(blueprint_env, temperature="15.5")
    assert blueprint_env.render("{{ states('sensor.room') | float > 15 }}") is True
    assert blueprint_env.render("{{ x * 2 }}", {"x": 4}) == 8


async def test_a_config_entry_can_be_used_by_template_functions(blueprint_env):
    # `config_entry_attr` needs an entry in the system; config_entries= adds it before the blueprint starts.
    entry = MockConfigEntry(domain="demo", title="Demo house")
    await start(blueprint_env, config_entries=[entry])
    assert blueprint_env.render(f"{{{{ config_entry_attr('{entry.entry_id}', 'title') }}}}") == "Demo house"


async def test_a_cold_room_switches_the_heater_on(blueprint_env):
    # The first branch: the call is switch.turn_on and its target is the heater, not just any switch.
    await start(blueprint_env)
    await blueprint_env.set_state(TEMPERATURE, "14")
    assert [call.name for call in blueprint_env.calls] == ["switch.turn_on"]
    assert blueprint_env.calls[0].entity_ids == {HEATER}


async def test_a_warm_room_switches_the_heater_off(blueprint_env):
    # The second branch: a running heater in a warm room is switched off, and the target is the heater.
    await start(blueprint_env, temperature="21", heater="on")
    await blueprint_env.set_state(TEMPERATURE, "22")
    assert [call.name for call in blueprint_env.calls] == ["switch.turn_off"]
    assert blueprint_env.calls[0].entity_ids == {HEATER}


async def test_opening_the_window_switches_a_running_heater_off(blueprint_env):
    # A cold room wants heat, but not with the window open.
    await start(blueprint_env, temperature="14", heater="on")
    await blueprint_env.set_state(WINDOW, "on")
    assert [call.name for call in blueprint_env.calls] == ["switch.turn_off"]


async def test_nothing_happens_when_the_heater_is_already_right(blueprint_env):
    # A cold room with the heater on, and a warm room with it off, need no call.
    await start(blueprint_env, temperature="15", heater="on")
    await blueprint_env.set_state(TEMPERATURE, "14")
    await blueprint_env.set_state(TEMPERATURE, "25")
    assert [call.name for call in blueprint_env.calls] == ["switch.turn_off"]  # only the warm room changes anything


async def test_the_limit_is_exclusive_and_defaults_to_19(blueprint_env):
    # Exactly 19 degrees is not "below 19"; 18.5 is. 19.5 must not switch on either (a limit of 20 would).
    await start(blueprint_env, temperature="25")
    await blueprint_env.set_state(TEMPERATURE, "19")
    await blueprint_env.set_state(TEMPERATURE, "19.5")
    assert blueprint_env.calls == []
    await blueprint_env.set_state(TEMPERATURE, "18.5")
    assert [call.name for call in blueprint_env.calls] == ["switch.turn_on"]
