import pytest

from quacc import SETTINGS, flow, job, subflow

ct = pytest.importorskip("covalent")
pytestmark = pytest.mark.skipif(
    SETTINGS.WORKFLOW_ENGINE != "covalent",
    reason="This test requires the Covalent workflow engine",
)


def test_covalent_decorators(tmpdir):
    tmpdir.chdir()

    @job
    def add(a, b):
        return a + b

    @job
    def mult(a, b):
        return a * b

    @job
    def make_more(val):
        return [val] * 3

    @subflow
    def add_distributed(vals, c):
        return [add(val, c) for val in vals]

    @flow
    def workflow(a, b, c):
        return mult(add(a, b), c)

    @flow
    def dynamic_workflow(a, b, c):
        result1 = add(a, b)
        result2 = make_more(result1)
        return add_distributed(result2, c)

    assert add(1, 2) == 3
    assert mult(1, 2) == 2
    assert ct.get_result(ct.dispatch(workflow)(1, 2, 3), wait=True).result == 9
    assert ct.get_result(ct.dispatch(dynamic_workflow)(1, 2, 3), wait=True).result == [
        6,
        6,
        6,
    ]
    assert ct.get_result(
        ct.dispatch(flow(add_distributed))([1, 1, 1], 2), wait=True
    ).result == [3, 3, 3]


def test_covalent_decorators_args(tmpdir):
    tmpdir.chdir()

    @job(executor="local")
    def add(a, b):
        return a + b

    @job(executor="local")
    def mult(a, b):
        return a * b

    @job(executor="local")
    def make_more(val):
        return [val] * 3

    @subflow(executor="local")
    def add_distributed(vals, c):
        return [add(val, c) for val in vals]

    @flow(executor="local")
    def workflow(a, b, c):
        return mult(add(a, b), c)

    @flow(executor="local")
    def dynamic_workflow(a, b, c):
        result1 = add(a, b)
        result2 = make_more(result1)
        return add_distributed(result2, c)

    assert add(1, 2) == 3
    assert mult(1, 2) == 2
    assert ct.get_result(ct.dispatch(workflow)(1, 2, 3), wait=True).result == 9
    assert ct.get_result(ct.dispatch(dynamic_workflow)(1, 2, 3), wait=True).result == [
        6,
        6,
        6,
    ]


def test_settings(tmpdir):
    tmpdir.chdir()

    @job
    def test_job():
        from quacc import SETTINGS

        return SETTINGS.GAUSSIAN_CMD

    @flow
    def workflow():
        from quacc import SETTINGS

        SETTINGS.GAUSSIAN_CMD = "test"
        return test_job()

    dispatch_id = ct.dispatch(workflow)()
    result = ct.get_result(dispatch_id, wait=True)
    assert result.result == "test"
