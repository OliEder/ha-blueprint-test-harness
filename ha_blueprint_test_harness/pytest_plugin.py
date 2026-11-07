import pathlib

import pytest

from .env import BlueprintEnv


# The fixture tests ask for to get a fresh environment: a Home Assistant instance (`hass`), an empty
# temporary config folder (`tmp_path`) and a clock that stands still until a test moves it (`freezer`).
@pytest.fixture
def blueprint_env(hass, tmp_path: pathlib.Path, freezer) -> BlueprintEnv:
    return BlueprintEnv(hass, tmp_path, freezer)
