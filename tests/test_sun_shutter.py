"""Reference automation tests: sun_shutter.yaml, a shutter that follows the sun.

Covers `numeric_state` triggers and conditions (on states and on attributes), trigger ids that select a `choose` branch,
nested `or`, and the `default` branch with `stop`.
"""

import pathlib

AUTOMATION = pathlib.Path(__file__).parent / "automations" / "sun_shutter.yaml"
SHUTTER, ELEVATION, AZIMUTH = "cover.shutter", "sensor.sun_elevation", "sensor.sun_azimuth"


# Starts the automation: shutter state and position, outside temperature, and where the sun is (azimuth in the sun entity).
async def start(env, position=100, state="open", temperature=25.0, azimuth=50.0, elevation="10", azimuth_sensor="50"):
    states = {
        ELEVATION: elevation, AZIMUTH: azimuth_sensor,
        "sun.sun": ("above_horizon", {"azimuth": azimuth}),
        "weather.home": ("sunny", {"temperature": temperature}),
        SHUTTER: (state, {"current_position": position}),
    }
    await env.start_automation(AUTOMATION, states=states, services=["cover.set_cover_position", "cover.open_cover"])


# The positions the shutter was asked to move to.
def positions(env):
    return [call.data["position"] for call in env.calls_to("cover.set_cover_position")]


async def test_a_hot_day_with_the_sun_on_the_window_side_lowers_an_open_shutter_to_30(blueprint_env):
    await start(blueprint_env)
    await blueprint_env.set_state(ELEVATION, "16")
    assert positions(blueprint_env) == [30]
    assert [call.entity_ids for call in blueprint_env.calls_to("cover.set_cover_position")] == [{SHUTTER}]


async def test_a_shutter_that_is_already_at_30_stays(blueprint_env):
    await start(blueprint_env, position=30)
    await blueprint_env.set_state(ELEVATION, "16")
    assert positions(blueprint_env) == []


async def test_a_shutter_that_is_nearly_closed_is_not_opened_to_30(blueprint_env):
    await start(blueprint_env, position=10)
    await blueprint_env.set_state(ELEVATION, "16")
    assert positions(blueprint_env) == []


async def test_a_shutter_just_above_30_is_lowered(blueprint_env):
    await start(blueprint_env, position=31)
    await blueprint_env.set_state(ELEVATION, "16")
    assert positions(blueprint_env) == [30]


async def test_a_cool_day_does_nothing(blueprint_env):
    await start(blueprint_env, temperature=23.0)
    await blueprint_env.set_state(ELEVATION, "16")
    assert positions(blueprint_env) == []


async def test_just_above_23_degrees_is_hot(blueprint_env):
    await start(blueprint_env, temperature=23.1)
    await blueprint_env.set_state(ELEVATION, "16")
    assert positions(blueprint_env) == [30]


async def test_the_sun_on_the_other_side_does_nothing(blueprint_env):
    await start(blueprint_env, azimuth=200.0)
    await blueprint_env.set_state(ELEVATION, "16")
    assert positions(blueprint_env) == []


async def test_the_sun_just_inside_the_window_side_from_the_north_counts(blueprint_env):
    await start(blueprint_env, azimuth=345.0)
    await blueprint_env.set_state(ELEVATION, "16")
    assert positions(blueprint_env) == [30]


async def test_the_sun_exactly_at_the_edges_does_not_count(blueprint_env):
    await start(blueprint_env, azimuth=340.0)
    await blueprint_env.set_state(ELEVATION, "16")
    assert positions(blueprint_env) == []


async def test_a_low_sun_does_not_trigger(blueprint_env):
    await start(blueprint_env)
    await blueprint_env.set_state(ELEVATION, "15")
    assert blueprint_env.calls == []


async def test_the_shutter_opens_when_the_sun_has_left_the_window_side(blueprint_env):
    await start(blueprint_env, state="open", elevation="20", azimuth=150.0)
    await blueprint_env.set_state(AZIMUTH, "150")
    assert len(blueprint_env.calls_to("cover.open_cover")) == 1
    assert [call.entity_ids for call in blueprint_env.calls_to("cover.open_cover")] == [{SHUTTER}]


async def test_a_closed_shutter_stays_closed_when_the_sun_leaves(blueprint_env):
    await start(blueprint_env, state="closed", position=0, elevation="20", azimuth=150.0)
    await blueprint_env.set_state(AZIMUTH, "150")
    assert blueprint_env.calls == []


async def test_the_shutter_does_not_open_when_the_sun_is_low(blueprint_env):
    await start(blueprint_env, state="open", elevation="10", azimuth=150.0)
    await blueprint_env.set_state(AZIMUTH, "150")
    assert blueprint_env.calls == []


async def test_the_sun_moving_within_the_window_side_does_not_open(blueprint_env):
    await start(blueprint_env, state="open", elevation="20", azimuth=50.0)
    await blueprint_env.set_state(AZIMUTH, "60")
    assert blueprint_env.calls == []


async def test_the_run_ends_in_the_default_branch_when_nothing_matches(blueprint_env):
    await start(blueprint_env, temperature=15.0)
    await blueprint_env.set_state(ELEVATION, "16")
    assert "action/0/default/0" in blueprint_env.last_trace().path


async def test_the_sun_moving_to_the_north_side_does_not_open(blueprint_env):
    # Above 340 degrees the sun is on the window side again (the other end of the range): no opening there.
    await start(blueprint_env, state="open", elevation="20", azimuth=350.0)
    await blueprint_env.set_state(AZIMUTH, "350")
    assert blueprint_env.calls == []
