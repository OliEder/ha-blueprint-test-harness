"""Canary for the Home Assistant internals that last_trace() reads. If a new Home Assistant version moves them,
this test fails and names what changed, so the fix is in one function of env.py."""

import pathlib

EXAMPLE = pathlib.Path(__file__).parents[1] / "docs" / "examples" / "window_heater.yaml"


async def test_the_trace_store_still_has_the_shape_last_trace_reads(blueprint_env):
    # last_trace() needs: hass.data["trace"][<key>].runs, a trace with as_extended_dict(), and the keys run_id and trace.
    from homeassistant.components.trace.const import DATA_TRACE

    await blueprint_env.start(
        EXAMPLE, {"room_temperature": "sensor.room", "window": "binary_sensor.window", "heater": "switch.heater"},
        states={"sensor.room": "15", "binary_sensor.window": "off", "switch.heater": "off"}, services=["switch.turn_on"],
    )
    await blueprint_env.set_state("sensor.room", "14")
    bucket = blueprint_env.hass.data[DATA_TRACE]["automation.blueprint_under_test"]
    data = list(bucket.runs.values())[-1].as_extended_dict()
    assert {"run_id", "trace"} <= set(data)
    element = next(iter(data["trace"].values()))[0]
    assert "changed_variables" in element, "a trace element no longer carries changed_variables"
