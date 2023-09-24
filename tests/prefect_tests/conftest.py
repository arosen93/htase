import importlib

import pytest


@pytest.fixture(autouse=True)
def reload_prefect_quacc(default_settings):
    importlib.reload(importlib.import_module("quacc"))
    from quacc import SETTINGS

    SETTINGS.WORKFLOW_ENGINE = "prefect"
    SETTINGS.SCRATCH_DIR = default_settings.SCRATCH_DIR
    SETTINGS.RESULTS_DIR = default_settings.RESULTS_DIR
