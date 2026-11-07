import pytest

# Makes pytest load our fixtures (`blueprint_env`) for every test in this project.
pytest_plugins = ["ha_blueprint_test_harness.pytest_plugin"]


# Home Assistant's test setup complains when timers are still armed after a test. Blueprints with state,
# time_pattern or sun triggers always leave some, so tell it that this is expected here.
@pytest.fixture
def expected_lingering_timers() -> bool:
    # State, time_pattern and sun triggers keep timers armed until Home Assistant stops.
    return True
