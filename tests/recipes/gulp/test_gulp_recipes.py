import os
from pathlib import Path
from shutil import copy, rmtree
import pytest
import numpy as np
from ase.build import bulk, molecule
from jobflow.managers.local import run_locally

from quacc.recipes.gulp.core import RelaxJob, StaticJob

FILE_DIR = Path(__file__).resolve().parent
GULP_DIR = os.path.join(FILE_DIR, "gulp_run")


def setup_module():
    for f in os.listdir(GULP_DIR):
        copy(os.path.join(GULP_DIR, f), os.path.join(os.getcwd(), f))


def teardown_module():
    for f in os.listdir(GULP_DIR):
        if os.path.exists(os.path.join(os.getcwd(), f)):
            os.remove(os.path.join(os.getcwd(), f))
    for f in os.listdir(os.getcwd()):
        if "quacc-tmp" in f or f == "tmp_dir":
            if os.path.islink(f):
                os.unlink(f)
            else:
                rmtree(f)


def test_static_Job():
    atoms = molecule("H2O")

    job = StaticJob().make(atoms)
    responses = run_locally(job, ensure_success=True)
    output = responses[job.uuid][1].output
    assert output["nsites"] == len(atoms)
    assert output["name"] == "GULP-Static"
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["keywords"] == "gfnff"
    assert "gwolf" not in output["parameters"]["keywords"]
    assert "dump every gulp.res" in output["parameters"]["options"]
    assert "output xyz gulp.xyz" in output["parameters"]["options"]
    assert "output cif gulp.cif" not in output["parameters"]["options"]
    assert output["results"]["energy"] == pytest.approx(49.82067095)
    assert np.array_equal(output["atoms"].get_positions(), atoms.get_positions())

    job = StaticJob(keyword_swaps={"gwolf": True}).make(atoms)
    responses = run_locally(job, ensure_success=True)
    output = responses[job.uuid][1].output
    assert output["nsites"] == len(atoms)
    assert output["name"] == "GULP-Static"
    assert output["nsites"] == len(atoms)
    assert "gfnff" in output["parameters"]["keywords"]
    assert "gwolf" in output["parameters"]["keywords"]
    assert "dump every gulp.res" in output["parameters"]["options"]
    assert "output xyz gulp.xyz" in output["parameters"]["options"]
    assert "output cif gulp.cif" not in output["parameters"]["options"]
    assert output["results"]["energy"] == pytest.approx(49.91178074)
    assert np.array_equal(output["atoms"].get_positions(), atoms.get_positions())

    job = StaticJob(keyword_swaps={"gfnff": False}).make(atoms)
    responses = run_locally(job, ensure_success=True)
    output = responses[job.uuid][1].output
    assert output["nsites"] == len(atoms)
    assert output["name"] == "GULP-Static"
    assert output["nsites"] == len(atoms)
    assert "gfnff" not in output["parameters"]["keywords"]
    assert "gwolf" not in output["parameters"]["keywords"]
    assert "dump every gulp.res" in output["parameters"]["options"]
    assert "output xyz gulp.xyz" in output["parameters"]["options"]
    assert "output cif gulp.cif" not in output["parameters"]["options"]
    assert output["results"]["energy"] == pytest.approx(4.08519509)
    assert np.array_equal(output["atoms"].get_positions(), atoms.get_positions())

    # atoms = bulk("Cu") * (2, 2, 2)
    # job = StaticJob().make(atoms)
    # responses = run_locally(job, ensure_success=True)
    # output = responses[job.uuid][1].output
    # assert output["nsites"] == len(atoms)
    # assert output["name"] == "GULP-Static"
    # assert output["parameters"]["keywords"] == "gfnff"
    # assert "gwolf" in output["parameters"]["keywords"]
    # assert "dump every gulp.res" in output["parameters"]["options"]
    # assert "output xyz gulp.xyz" not in output["parameters"]["options"]
    # assert "output cif gulp.cif" in output["parameters"]["options"]
    # assert output["results"]["energy"] == pytest.approx(49.82067095)
    # assert np.array_equal(output["atoms"].get_positions(), atoms.get_positions())

    # job = StaticJob(keyword_swaps={"gwolf": False}).make(atoms)
    # responses = run_locally(job, ensure_success=True)
    # output = responses[job.uuid][1].output
    # assert output["nsites"] == len(atoms)
    # assert output["name"] == "GULP-Static"
    # assert "gfnff" in output["parameters"]["keywords"]
    # assert "gwolf" not in output["parameters"]["keywords"]
    # assert "dump every gulp.res" in output["parameters"]["options"]
    # assert "output xyz gulp.xyz" not in output["parameters"]["options"]
    # assert "output cif gulp.cif" in output["parameters"]["options"]
    # assert output["results"]["energy"] == pytest.approx(49.91178074)
    # assert np.array_equal(output["atoms"].get_positions(), atoms.get_positions())

    # job = StaticJob(keyword_swaps={"gfnff": False}).make(atoms)
    # responses = run_locally(job, ensure_success=True)
    # output = responses[job.uuid][1].output
    # assert output["nsites"] == len(atoms)
    # assert output["name"] == "GULP-Static"
    # assert "gfnff" not in output["parameters"]["keywords"]
    # assert "gwolf" not in output["parameters"]["keywords"]
    # assert "dump every gulp.res" in output["parameters"]["options"]
    # assert "output xyz gulp.xyz" not in output["parameters"]["options"]
    # assert "output cif gulp.cif" in output["parameters"]["options"]
    # assert output["results"]["energy"] == pytest.approx(4.08519509)
    # assert np.array_equal(output["atoms"].get_positions(), atoms.get_positions())


def test_relax_Job():
    atoms = molecule("H2O")

    job = RelaxJob().make(atoms)
    responses = run_locally(job, ensure_success=True)
    output = responses[job.uuid][1].output
    assert output["nsites"] == len(atoms)
    assert output["name"] == "GULP-Relax"
    assert "gfnff" in output["parameters"]["keywords"]
    assert "opti" in output["parameters"]["keywords"]
    assert "conp" not in output["parameters"]["keywords"]
    assert "conv" in output["parameters"]["keywords"]
    assert "gwolf" not in output["parameters"]["keywords"]
    assert "dump every gulp.res" in output["parameters"]["options"]
    assert "output xyz gulp.xyz" in output["parameters"]["options"]
    assert "output cif gulp.cif" not in output["parameters"]["options"]
    assert output["results"]["energy"] == pytest.approx(49.07911539)
    assert not np.array_equal(output["atoms"].get_positions(), atoms.get_positions())

    job = RelaxJob(volume_relax=False, keyword_swaps={"gwolf": True}).make(atoms)
    responses = run_locally(job, ensure_success=True)
    output = responses[job.uuid][1].output
    assert output["nsites"] == len(atoms)
    assert output["name"] == "GULP-Relax"
    assert output["nsites"] == len(atoms)
    assert "gfnff" in output["parameters"]["keywords"]
    assert "opti" in output["parameters"]["keywords"]
    assert "conp" not in output["parameters"]["keywords"]
    assert "conv" in output["parameters"]["keywords"]
    assert "gwolf" in output["parameters"]["keywords"]
    assert "dump every gulp.res" in output["parameters"]["options"]
    assert "output xyz gulp.xyz" in output["parameters"]["options"]
    assert "output cif gulp.cif" not in output["parameters"]["options"]
    assert output["results"]["energy"] == pytest.approx(49.25776173)
    assert not np.array_equal(output["atoms"].get_positions(), atoms.get_positions())

    job = RelaxJob(keyword_swaps={"gfnff": False}).make(atoms)
    responses = run_locally(job, ensure_success=True)
    output = responses[job.uuid][1].output
    assert output["nsites"] == len(atoms)
    assert output["name"] == "GULP-Relax"
    assert output["nsites"] == len(atoms)
    assert "gfnff" not in output["parameters"]["keywords"]
    assert "opti" in output["parameters"]["keywords"]
    assert "conp" not in output["parameters"]["keywords"]
    assert "conv" in output["parameters"]["keywords"]
    assert "gwolf" not in output["parameters"]["keywords"]
    assert "dump every gulp.res" in output["parameters"]["options"]
    assert "output xyz gulp.xyz" in output["parameters"]["options"]
    assert "output cif gulp.cif" not in output["parameters"]["options"]
    assert output["results"]["energy"] == pytest.approx(0.00393618)
    assert not np.array_equal(output["atoms"].get_positions(), atoms.get_positions())
