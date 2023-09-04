from typer.testing import CliRunner

from quacc._cli.quacc import app
from quacc import __version__
from quacc import SETTINGS
from pathlib import Path
import os
DEFAULT_SETTINGS= SETTINGS.copy()
test_yaml = Path.cwd()/"test_quacc.yaml"
def setup_module():

    SETTINGS.CONFIG_FILE = test_yaml
def teardown_module():
    SETTINGS=DEFAULT_SETTINGS
    if test_yaml.exists():
        os.remove(test_yaml)

runner = CliRunner()

def test_version():
    response = runner.invoke(app,["--version"])
    assert response.exit_code==0
    assert __version__ in response.stdout

def test_help():
    response = runner.invoke(app,["--help"])
    assert response.exit_code==0

def test_set():
    response = runner.invoke(app,["set","WORKFLOW_ENGINE","local"])
    assert response.exit_code==0
    assert "local" in response.stdout
    val = None
    with open(test_yaml,"r") as f:
        for line in f:
            if "WORKFLOW_ENGINE" in line:
                val = line.split(":")[-1].strip()
    assert val=="local"

    response = runner.invoke(app,["set","WORKFLOW_ENGINE","covalent"])
    assert response.exit_code==0
    assert "covalent" in response.stdout
    val = None
    with open(test_yaml,"r") as f:
        for line in f:
            if "WORKFLOW_ENGINE" in line:
                val = line.split(":")[-1].strip()
    assert val=="covalent"

def test_unset():
    response = runner.invoke(app,["unset","WORKFLOW_ENGINE"])
    assert response.exit_code==0
    assert "WORKFLOW_ENGINE" in response.stdout
    lines = ""
    with open(test_yaml,"r") as f:
        for line in f:
            lines+=""
            if "WORKFLOW_ENGINE" in line:
                val = line.split(":")[-1].strip()
    assert "WORKFLOW_ENGINE" not in lines