from __future__ import annotations

import os
from importlib import util
from logging import WARNING, getLogger
from pathlib import Path
from shutil import copytree, move

import pytest
from ase.io import read
from maggma.stores import MemoryStore
from monty.json import MontyDecoder, jsanitize

from quacc.calculators.vasp import Vasp
from quacc.schemas.vasp import VaspSummarize

LOGGER = getLogger(__name__)
LOGGER.propagate = True
has_pmg_validation = util.find_spec("pymatgen.io.validation") is not None


@pytest.fixture
def run1():
    FILE_DIR = Path(__file__).parent

    return FILE_DIR / "test_files" / "vasp_run1"


@pytest.fixture
def mp_run1():
    FILE_DIR = Path(__file__).parent

    return FILE_DIR / "test_files" / "vasp_mp_run1"


def mock_bader_analysis(*args, **kwargs):
    return {
        "min_dist": [1.0] * 16,
        "charge": [1.0] * 16,
        "atomic_volume": [1.0] * 16,
        "vacuum_charge": 1.0,
        "vacuum_volume": 1.0,
        "bader_version": 1.0,
        "reference_used": [0.0] * 16,
        "charge_transfer": [-1.0] * 16,
        "magmom": [0.0] * 16,
    }


def mock_chargemol_analysis(*args, **kwargs):
    return {
        "ddec": {
            "partial_charges": [1.0] * 16,
            "spin_moments": [0.0] * 16,
            "dipoles": [1.0] * 16,
            "rsquared_moments": [1.0] * 16,
            "rcubed_moments": [1.0] * 16,
            "rfourth_moments": [1.0] * 16,
        },
        "cm5": {"partial_charges": [1.0] * 16},
    }


def test_vasp_summarize_run(run1, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    p = tmp_path / "vasp_run"
    copytree(run1, p)

    atoms = read(os.path.join(p, "OUTCAR.gz"))
    calc = atoms.calc
    results = VaspSummarize(directory=p).run(atoms)
    assert results["nsites"] == len(atoms)
    assert results["atoms"] == atoms
    assert results["output"]["energy"] == -33.15807349
    assert Path(results["dir_name"]).is_dir()
    assert "calcs_reversed" in results
    assert "orig_inputs" in results

    # Make sure default dir works
    monkeypatch.chdir(p)
    VaspSummarize().run(atoms)
    monkeypatch.chdir(tmp_path)

    # Test DB
    atoms = read(os.path.join(p, "OUTCAR.gz"))
    store = MemoryStore()
    VaspSummarize(directory=p).run(atoms, store=store)
    assert store.count() == 1

    # Make sure metadata is made
    atoms = read(os.path.join(run1, "OUTCAR.gz"))
    results = VaspSummarize(directory=p, additional_fields={"test": "hi"}).run(atoms)
    assert results.get("test") == "hi"

    # Make sure info tags are handled appropriately
    atoms = read(os.path.join(run1, "CONTCAR.gz"))
    calc = Vasp(atoms)
    atoms.calc = calc
    atoms.calc.results = {"energy": -1.0}
    atoms.info["test_dict"] = {"hi": "there", "foo": "bar"}
    results = VaspSummarize(directory=p).run(atoms)
    results_atoms = results["atoms"]
    assert atoms.info.get("test_dict", None) == {"hi": "there", "foo": "bar"}
    assert results_atoms.info.get("test_dict", None) == {"hi": "there", "foo": "bar"}

    # Make sure magnetic moments are handled appropriately
    atoms = read(os.path.join(run1, "CONTCAR.gz"))
    atoms.set_initial_magnetic_moments([3.14] * len(atoms))
    calc = Vasp(atoms)
    atoms.calc = calc
    atoms.calc.results = {"energy": -1.0, "magmoms": [2.0] * len(atoms)}
    results = VaspSummarize(directory=p).run(atoms)
    results_atoms = results["atoms"]

    assert atoms.calc is not None
    assert atoms.get_initial_magnetic_moments().tolist() == [3.14] * len(atoms)

    assert results_atoms.get_initial_magnetic_moments().tolist() == [2.0] * len(atoms)
    assert results_atoms.calc is None

    # Make sure Atoms magmoms were not moved if specified
    atoms = read(os.path.join(run1, "CONTCAR.gz"))
    calc = Vasp(atoms)
    atoms.calc = calc
    atoms.calc.results = {"energy": -1.0}
    atoms.set_initial_magnetic_moments([3.14] * len(atoms))
    results = VaspSummarize(directory=p, move_magmoms=False).run(atoms)
    assert atoms.get_initial_magnetic_moments().tolist() == [3.14] * len(atoms)
    results_atoms = results["atoms"]
    assert results_atoms.get_initial_magnetic_moments().tolist() == [3.14] * len(atoms)

    # test document can be jsanitized and decoded
    d = jsanitize(results, strict=True, enum_values=True)
    MontyDecoder().process_decoded(d)


def test_summarize_bader_run(monkeypatch, run1, tmp_path):
    monkeypatch.setattr(
        "quacc.schemas.vasp.bader_analysis_from_path", mock_bader_analysis
    )
    monkeypatch.chdir(tmp_path)

    p = tmp_path / "vasp_run"
    copytree(run1, p)

    move(p / "garbled_pot", p / "POTCAR")

    for f in ["CHGCAR.gz", "AECCAR0.gz", "AECCAR2.gz"]:
        with open(p / f, "w") as w:
            w.write("test")

    # Make sure Bader works
    atoms = read(str(p / "OUTCAR.gz"))
    results = VaspSummarize(directory=p, run_bader=True).run(atoms)
    assert results["bader"]["partial_charges"] == [1.0] * len(atoms)
    assert results["bader"]["spin_moments"] == [0.0] * len(atoms)


def test_summarize_chargemol_run(monkeypatch, run1, tmp_path):
    monkeypatch.setattr("quacc.schemas.vasp.ChargemolAnalysis", mock_chargemol_analysis)
    monkeypatch.setenv("DDEC6_ATOMIC_DENSITIES_DIR", "test")
    monkeypatch.chdir(tmp_path)

    p = tmp_path / "vasp_run"
    copytree(run1, p)

    move(p / "garbled_pot", p / "POTCAR")

    for f in ["CHGCAR.gz", "AECCAR0.gz", "AECCAR2.gz"]:
        with open(p / f, "w") as w:
            w.write("test")

    # Make sure Bader works
    atoms = read(str(p / "OUTCAR.gz"))
    results = VaspSummarize(directory=p, run_bader=False, run_chargemol=True).run(atoms)
    assert results["chargemol"]["ddec"]["partial_charges"] == [1.0] * len(atoms)
    assert results["chargemol"]["cm5"]["partial_charges"] == [1.0] * len(atoms)
    assert results["chargemol"]["ddec"]["spin_moments"] == [0.0] * len(atoms)


def test_summarize_bader_and_chargemol_run(monkeypatch, run1, tmp_path):
    monkeypatch.setattr(
        "quacc.schemas.vasp.bader_analysis_from_path", mock_bader_analysis
    )
    monkeypatch.setattr("quacc.schemas.vasp.ChargemolAnalysis", mock_chargemol_analysis)
    monkeypatch.setenv("DDEC6_ATOMIC_DENSITIES_DIR", "test")
    monkeypatch.chdir(tmp_path)

    p = tmp_path / "vasp_run"
    copytree(run1, p)

    move(p / "garbled_pot", p / "POTCAR")

    for f in ["CHGCAR.gz", "AECCAR0.gz", "AECCAR2.gz"]:
        with open(p / f, "w") as w:
            w.write("test")

    # Make sure Bader works
    atoms = read(str(p / "OUTCAR.gz"))
    results = VaspSummarize(directory=p, run_bader=True, run_chargemol=True).run(atoms)
    assert results["chargemol"]["ddec"]["partial_charges"] == [1.0] * len(atoms)
    assert results["chargemol"]["cm5"]["partial_charges"] == [1.0] * len(atoms)
    assert results["chargemol"]["ddec"]["spin_moments"] == [0.0] * len(atoms)
    assert results["bader"]["partial_charges"] == [1.0] * len(atoms)
    assert results["bader"]["spin_moments"] == [0.0] * len(atoms)


@pytest.mark.skipif(
    not has_pmg_validation, reason="pymatgen-io-validation not installed"
)
def test_validate_mp(monkeypatch, mp_run1, tmp_path, caplog):
    monkeypatch.chdir(tmp_path)
    p = tmp_path / "vasp_mp_run"
    copytree(mp_run1, p)
    atoms = read(p / "OUTCAR.gz")
    with caplog.at_level(WARNING):
        results = VaspSummarize(directory=p, check_mp_compatibility=True).run(atoms)
    assert "Incorrect POTCAR files were used" in caplog.text
    assert "Incorrect POTCAR files were used" in " ".join(
        results["validation"]["reasons"]
    )
    assert results["validation"]["valid"] is False


def test_no_bader(tmp_path, monkeypatch, run1, caplog):
    monkeypatch.chdir(tmp_path)
    p = tmp_path / "vasp_run"
    copytree(run1, p)
    atoms = read(p / "OUTCAR.gz")
    with caplog.at_level(WARNING):
        VaspSummarize(directory=p, run_bader=True, run_chargemol=False).run(atoms)
    assert "Bader analysis could not be performed." in caplog.text


def test_no_chargemol(tmp_path, monkeypatch, run1, caplog):
    monkeypatch.chdir(tmp_path)
    p = tmp_path / "vasp_run"
    copytree(run1, p)
    atoms = read(p / "OUTCAR.gz")
    with caplog.at_level(WARNING):
        VaspSummarize(directory=p, run_bader=False, run_chargemol=True).run(atoms)
    assert "Chargemol analysis could not be performed." in caplog.text
