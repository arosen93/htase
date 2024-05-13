from __future__ import annotations

from ase.build import molecule
from numpy.testing import assert_array_equal

from quacc.recipes.gaussian.core import relax_job, static_job


def test_static_job():
    atoms = molecule("H2")

    output = static_job(atoms, 0, 1)
    assert output["natoms"] == len(atoms)
    assert output["parameters"]["charge"] == 0
    assert output["parameters"]["mult"] == 1
    assert output["parameters"]["force"] == ""
    assert output["parameters"]["xc"] == "wb97xd"
    assert output["parameters"]["basis"] == "def2tzvp"
    assert output["parameters"]["integral"] == "ultrafine"
    assert output["parameters"]["gfinput"] == ""
    assert output["parameters"]["ioplist"] == [
        "6/7=3",
        "2/9=2000",
    ]  # see ASE issue #660

    output = static_job(
        atoms, -2, 3, xc="m06l", basis="def2svp", integral="superfinegrid"
    )
    assert output["natoms"] == len(atoms)
    assert output["parameters"]["charge"] == -2
    assert output["parameters"]["mult"] == 3
    assert output["parameters"]["force"] == ""
    assert output["parameters"]["xc"] == "m06l"
    assert output["parameters"]["basis"] == "def2svp"
    assert output["parameters"]["integral"] == "superfinegrid"
    assert output["parameters"]["gfinput"] == ""
    assert output["parameters"]["ioplist"] == [
        "6/7=3",
        "2/9=2000",
    ]  # see ASE issue #660
    assert "opt" not in output["parameters"]
    assert_array_equal(output["atoms"].get_initial_magnetic_moments(), [0, 0])


def test_relax_job():
    atoms = molecule("H2")
    atoms.set_initial_magnetic_moments([0, 0])

    output = relax_job(atoms, 0, 1)
    assert output["natoms"] == len(atoms)
    assert output["parameters"]["charge"] == 0
    assert output["parameters"]["mult"] == 1
    assert output["parameters"]["opt"] == ""
    assert output["parameters"]["xc"] == "wb97xd"
    assert output["parameters"]["basis"] == "def2tzvp"
    assert output["parameters"]["integral"] == "ultrafine"
    assert "freq" not in output["parameters"]
    assert "sp" not in output["parameters"]

    output = relax_job(
        atoms, -2, 3, xc="m06l", basis="def2svp", freq=True, integral="superfinegrid"
    )
    assert output["natoms"] == len(atoms)
    assert output["parameters"]["charge"] == -2
    assert output["parameters"]["mult"] == 3
    assert output["parameters"]["opt"] == ""
    assert output["parameters"]["freq"] == ""
    assert output["parameters"]["xc"] == "m06l"
    assert output["parameters"]["basis"] == "def2svp"
    assert output["parameters"]["integral"] == "superfinegrid"
    assert output["parameters"]["ioplist"] == ["2/9=2000"]  # see ASE issue #660
    assert_array_equal(output["atoms"].get_initial_magnetic_moments(), [0, 0])


def test_relax_job_v2():
    atoms = molecule("H2")
    atoms.set_initial_magnetic_moments([0, 3])

    output = relax_job(atoms, 0, 3)
    assert output["natoms"] == len(atoms)
    assert output["parameters"]["charge"] == 0
    assert output["parameters"]["mult"] == 3
    assert output["parameters"]["opt"] == ""
    assert output["parameters"]["xc"] == "wb97xd"
    assert output["parameters"]["basis"] == "def2tzvp"
    assert output["parameters"]["integral"] == "ultrafine"
    assert "freq" not in output["parameters"]
    assert "sp" not in output["parameters"]
    assert_array_equal(output["atoms"].get_initial_magnetic_moments(), [0, 3])
