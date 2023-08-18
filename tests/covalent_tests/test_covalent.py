from quacc import SETTINGS

DEFAULT_SETTINGS = SETTINGS.copy()

SETTINGS.WORKFLOW_ENGINE = "covalent"
import os

import pytest
from ase.build import bulk, molecule

from quacc import flow, job, subflow
from quacc.recipes.emt.core import relax_job, static_job
from quacc.recipes.emt.slabs import bulk_to_slabs_flow

try:
    import covalent as ct
except ImportError:
    ct = None

os.system("covalent start")

def teardown_module():
    SETTINGS.WORKFLOW_ENGINE = DEFAULT_SETTINGS.WORKFLOW_ENGINE


@pytest.mark.skipif(
    ct is None,
    reason="This test is only meant to be run on GitHub Actions",
)
def test_quickstart(tmpdir):
    tmpdir.chdir()

    workflow_start = flow(relax_job)
    atoms = bulk("Cu")
    dispatch_id = ct.dispatch(workflow_start)(atoms)
    result = ct.get_result(dispatch_id, wait=True)
    assert result.status == "COMPLETED"

    @flow(executor="local")
    def workflow_start2(atoms):
        relaxed_bulk = relax_job(atoms)
        relaxed_slabs = bulk_to_slabs_flow(relaxed_bulk)
        return relaxed_slabs

    atoms = bulk("Cu")
    dispatch_id = ct.dispatch(workflow_start2)(atoms)
    result = ct.get_result(dispatch_id, wait=True)
    assert result.status == "COMPLETED"


@pytest.mark.skipif(
    ct is None,
    reason="This test is only meant to be run on GitHub Actions",
)
def test_tutorial1(tmpdir):
    tmpdir.chdir()

    # Define the workflow
    @flow
    def workflow(atoms):
        return relax_job(atoms)

    # Make an Atoms object of a bulk Cu structure
    atoms = bulk("Cu")

    # Dispatch the workflow to the Covalent server
    # with the bulk Cu Atoms object as the input
    dispatch_id = ct.dispatch(workflow)(atoms)

    # Fetch the result from the server
    result = ct.get_result(dispatch_id, wait=True)
    assert result.status == "COMPLETED"


@pytest.mark.skipif(
    ct is None,
    reason="This test is only meant to be run on GitHub Actions",
)
def test_tutorial2(tmpdir):
    tmpdir.chdir()

    # Define the workflow
    workflow = flow(relax_job)

    # Make an Atoms object of a bulk Cu structure
    atoms = bulk("Cu")

    # Dispatch the workflow to the Covalent server
    # with the bulk Cu Atoms object as the input
    dispatch_id = ct.dispatch(workflow)(atoms)

    # Fetch the result from the server
    result = ct.get_result(dispatch_id, wait=True)
    assert result.status == "COMPLETED"


@pytest.mark.skipif(
    ct is None,
    reason="This test is only meant to be run on GitHub Actions",
)
def test_tutorial3(tmpdir):
    tmpdir.chdir()

    @flow
    def workflow1(atoms):
        result1 = relax_job(atoms)
        result2 = static_job(result1)
        return result2

    atoms = bulk("Cu")
    dispatch_id = ct.dispatch(workflow1)(atoms)
    result = ct.get_result(dispatch_id, wait=True)
    assert result.status == "COMPLETED"


@pytest.mark.skipif(
    ct is None,
    reason="This test is only meant to be run on GitHub Actions",
)
def test_tutorial4(tmpdir):
    tmpdir.chdir()

    @flow
    def workflow2(atoms1, atoms2):
        result1 = relax_job(atoms1)
        result2 = relax_job(atoms2)

        return [result1, result2]

    atoms1 = bulk("Cu")
    atoms2 = molecule("N2")
    dispatch_id = ct.dispatch(workflow2)(atoms1, atoms2)
    result = ct.get_result(dispatch_id, wait=True)
    assert result.status == "COMPLETED"


@pytest.mark.skipif(
    ct is None,
    reason="This test is only meant to be run on GitHub Actions",
)
def test_tutorial5(tmpdir):
    tmpdir.chdir()

    @flow
    def workflow3(atoms):
        relaxed_bulk = relax_job(atoms)
        relaxed_slabs = bulk_to_slabs_flow(relaxed_bulk, slab_static=None)
        return relaxed_slabs

    atoms = bulk("Cu")
    dispatch_id = ct.dispatch(workflow3)(atoms)
    result = ct.get_result(dispatch_id, wait=True)
    assert result.status == "COMPLETED"


@pytest.mark.skipif(
    ct is None,
    reason="This test is only meant to be run on GitHub Actions",
)
def test_tutorial6(tmpdir):
    tmpdir.chdir()

    @flow(executor="local")
    def workflow4(atoms):
        result1 = relax_job(atoms)
        result2 = static_job(result1)
        return result2

    atoms = bulk("Cu")
    dispatch_id = ct.dispatch(workflow4)(atoms)
    result = ct.get_result(dispatch_id, wait=True)
    assert result.status == "COMPLETED"


@pytest.mark.skipif(
    ct is None,
    reason="This test is only meant to be run on GitHub Actions",
)
def test_tutorial7(tmpdir):
    tmpdir.chdir()

    @job
    def relax_electron(atoms):
        return relax_job(atoms)

    @job
    def static_electron(atoms):
        return static_job(atoms)

    @flow
    def workflow5(atoms):
        relax_electron.executor = "dask"
        static_electron.executor = "local"
        output1 = relax_electron(atoms)
        output2 = static_electron(output1)
        return output2

    atoms = bulk("Cu")
    dispatch_id = ct.dispatch(workflow5)(atoms)
    result = ct.get_result(dispatch_id, wait=True)
    assert result.status == "COMPLETED"


@pytest.mark.skipif(
    ct is None,
    reason="This test is only meant to be run on GitHub Actions",
)
def test_comparison1():
    @job
    def add(a, b):
        return a + b

    @job
    def mult(a, b):
        return a * b

    @flow
    def workflow(a, b, c):
        return mult(add(a, b), c)

    # Locally
    assert workflow(1, 2, 3) == 9

    # Dispatched
    dispatch_id = ct.dispatch(workflow)(1, 2, 3)
    result = ct.get_result(dispatch_id, wait=True)
    assert result.status == "COMPLETED"


@pytest.mark.skipif(
    ct is None,
    reason="This test is only meant to be run on GitHub Actions",
)
def test_comparison2():
    @job
    def add(a, b):
        return a + b

    @job
    def make_more(val):
        return [val] * 3

    @subflow
    def add_distributed(vals, c):
        return [add(val, c) for val in vals]

    @flow
    def workflow(a, b, c):
        result1 = add(a, b)
        result2 = make_more(result1)
        return add_distributed(result2, c)

    # Locally
    assert workflow(1, 2, 3) == [6, 6, 6]

    # Dispatched
    dispatch_id = ct.dispatch(workflow)(1, 2, 3)
    result = ct.get_result(dispatch_id, wait=True)
    assert result.status == "COMPLETED"
    assert result.status == "COMPLETED"
