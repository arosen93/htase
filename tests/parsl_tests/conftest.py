import importlib

import pytest


@pytest.fixture(autouse=True)
def reload_parsl_quacc(default_settings):
    importlib.reload(importlib.import_module("quacc"))
    from quacc import SETTINGS

    SETTINGS.WORKFLOW_ENGINE = "parsl"
    SETTINGS.SCRATCH_DIR = default_settings.SCRATCH_DIR
    SETTINGS.RESULTS_DIR = default_settings.RESULTS_DIR


@pytest.fixture(autouse=True)
def start_parsl():
    from parsl.dataflow.dflow import DataFlowKernelLoader
    from parsl.errors import ConfigurationError

    try:
        DataFlowKernelLoader.dfk()
    except ConfigurationError:
        import parsl

        parsl.load()
