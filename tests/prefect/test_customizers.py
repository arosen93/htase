from __future__ import annotations

import pytest

prefect = pytest.importorskip("prefect")

from pathlib import Path

from quacc import flow, get_settings, job, redecorate, strip_decorator, subflow
from quacc.wflow_tools.customizers import customize_funcs


def test_strip_decorators():
    @job
    def add(a, b):
        return a + b

    @flow
    def add2(a, b):
        return a + b

    @subflow
    def add3(a, b):
        return a + b

    stripped_add = strip_decorator(add)
    assert stripped_add(1, 2) == 3

    stripped_add2 = strip_decorator(add2)
    assert stripped_add2(1, 2) == 3

    stripped_add3 = strip_decorator(add3)
    assert stripped_add3(1, 2) == 3


def test_change_settings_redecorate_job(tmp_path_factory):
    tmp_dir1 = tmp_path_factory.mktemp("dir1")

    @job
    def write_file_job(name="job.txt"):
        with open(Path(get_settings().RESULTS_DIR, name), "w") as f:
            f.write("test file")

    write_file_job = redecorate(
        write_file_job, job(settings_swap={"RESULTS_DIR": tmp_dir1})
    )

    @flow
    def my_flow():
        return write_file_job()

    my_flow().result()
    assert Path(tmp_dir1 / "job.txt").exists()


def test_change_settings_redecorate_flow(tmp_path_factory):
    tmp_dir2 = tmp_path_factory.mktemp("dir2")

    @job
    def write_file_job(name="job.txt"):
        with open(Path(get_settings().RESULTS_DIR, name), "w") as f:
            f.write("test file")

    @flow
    def write_file_flow(name="flow.txt", job_decorators=None):
        write_file_job_ = customize_funcs(
            ["write_file_job"], [write_file_job], decorators=job_decorators
        )
        return write_file_job_(name=name)

    # Test with redecorating a job in a flow
    write_file_flow(
        job_decorators={"write_file_job": job(settings_swap={"RESULTS_DIR": tmp_dir2})}
    ).result()
    assert Path(tmp_dir2 / "flow.txt").exists()


def test_double_change_settings_redecorate_job(tmp_path_factory):
    tmp_dir1 = tmp_path_factory.mktemp("dir1")
    tmp_dir2 = tmp_path_factory.mktemp("dir2")

    @job
    def write_file_job(name="job.txt"):
        with open(Path(get_settings().RESULTS_DIR, name), "w") as f:
            f.write("test file")

    write_file_job = redecorate(
        write_file_job, job(settings_swap={"RESULTS_DIR": tmp_dir1})
    )
    write_file_job = redecorate(
        write_file_job, job(settings_swap={"RESULTS_DIR": tmp_dir2})
    )

    @flow
    def my_flow():
        return write_file_job()

    my_flow().result()
    assert not Path(tmp_dir1 / "job.txt").exists()
    assert Path(tmp_dir2 / "job.txt").exists()


def test_nested_output_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    @job
    def write_file_job(name="job.txt"):
        results_file_path = Path(get_settings().RESULTS_DIR, name)
        with open(results_file_path, "w") as f:
            f.write("test job file")

        return results_file_path

    @flow
    def write_file_flow(name="flow.txt"):
        job_results_file_path = write_file_job()

        flow_results_file_path = Path(get_settings().RESULTS_DIR, name)
        with open(flow_results_file_path, "w") as f:
            f.write("test flow file")

        return job_results_file_path, flow_results_file_path

    # Test with redecorating a job in a flow
    job_results_file_path, flow_results_file_path = write_file_flow()
    job_results_file_path = job_results_file_path.result()
    assert Path(job_results_file_path).exists()
    assert Path(flow_results_file_path).exists()

    # Check the job output is in a subfolder of the flow folder
    assert (
        Path(job_results_file_path).parent.parent == Path(flow_results_file_path).parent
    )
