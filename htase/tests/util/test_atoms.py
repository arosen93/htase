from ase.io import read
from ase.build import bulk
from ase.io.jsonio import encode, decode
from htase.util.atoms import (
    prep_next_run,
    get_atoms_id,
)
from htase.calculators.vasp import SmartVasp
from pathlib import Path
import os
from copy import deepcopy

FILE_DIR = Path(__file__).resolve().parent
ATOMS_MAG = read(os.path.join(FILE_DIR, "..", "calculators", "vasp", "OUTCAR_mag.gz"))
ATOMS_NOMAG = read(
    os.path.join(FILE_DIR, "..", "calculators", "vasp", "OUTCAR_nomag.gz")
)
ATOMS_NOSPIN = read(
    os.path.join(FILE_DIR, "..", "calculators", "vasp", "OUTCAR_nospin.gz")
)


def test_get_atoms_id():
    atoms = bulk("Cu")
    md5hash = "d4859270a1a67083343bec0ab783f774"
    assert get_atoms_id(atoms) == md5hash

    atoms.info["test"] = "hi"
    assert get_atoms_id(atoms) == md5hash

    atoms.set_initial_magnetic_moments([1.0])
    md5maghash = "7d456a48c235e05cf17da4abcc433a4f"
    assert get_atoms_id(atoms) == md5maghash


def test_prep_next_run():
    atoms = bulk("Cu")
    md5hash = "d4859270a1a67083343bec0ab783f774"
    atoms = prep_next_run(atoms)
    assert atoms.info.get("_id", None) == md5hash
    assert atoms.info.get("_old_ids", None) is None
    atoms = prep_next_run(atoms)
    assert atoms.info.get("_id", None) == md5hash
    assert atoms.info.get("_old_ids", None) == [md5hash]
    atoms[0].symbol = "Pt"
    new_md5hash = "52087d50a909572d58e01cfb49d4911b"
    atoms = prep_next_run(atoms)
    assert atoms.info.get("_old_ids", None) == [
        md5hash,
        md5hash,
    ]
    assert atoms.info.get("_id", None) == new_md5hash

    atoms = deepcopy(ATOMS_MAG)
    atoms.info["test"] = "hi"
    mag = atoms.get_magnetic_moment()
    init_mags = atoms.get_initial_magnetic_moments()
    mags = atoms.get_magnetic_moments()
    atoms = prep_next_run(atoms)
    assert atoms.info["test"] == "hi"
    assert atoms.calc == None
    assert atoms.get_initial_magnetic_moments().tolist() == mags.tolist()

    atoms = deepcopy(ATOMS_MAG)
    atoms.info["test"] = "hi"
    atoms = prep_next_run(atoms, store_results=True)
    assert atoms.info.get("test", None) == "hi"
    assert atoms.info.get("results", None) is not None
    assert atoms.info["results"].get("calc0", None) is not None
    assert atoms.info["results"]["calc0"]["magmom"] == mag
    atoms = SmartVasp(atoms)
    atoms.calc.results = {"magmom": mag - 2}
    atoms = prep_next_run(atoms, store_results=True)
    assert atoms.info.get("results", None) is not None
    assert atoms.info["results"].get("calc1", None) is not None
    assert atoms.info["results"]["calc0"]["magmom"] == mag
    assert atoms.info["results"]["calc1"]["magmom"] == mag - 2
    assert decode(encode(atoms)) == atoms

    atoms = deepcopy(ATOMS_MAG)
    atoms = prep_next_run(atoms, move_magmoms=False)
    assert atoms.get_initial_magnetic_moments().tolist() == init_mags.tolist()

    atoms = deepcopy(ATOMS_NOMAG)
    mag = atoms.get_magnetic_moment()
    atoms = prep_next_run(atoms, store_results=True)
    assert atoms.info.get("results", None) is not None
    assert atoms.info["results"].get("calc0", None) is not None
    assert atoms.info["results"]["calc0"]["magmom"] == mag
    atoms = SmartVasp(atoms)
    atoms.calc.results = {"magmom": mag - 2}
    atoms = prep_next_run(atoms, store_results=True)
    assert atoms.info.get("results", None) is not None
    assert atoms.info["results"].get("calc1", None) is not None
    assert atoms.info["results"]["calc0"]["magmom"] == mag
    assert atoms.info["results"]["calc1"]["magmom"] == mag - 2
    assert decode(encode(atoms)) == atoms

    atoms = deepcopy(ATOMS_NOSPIN)
    atoms = prep_next_run(atoms, store_results=True)
    assert atoms.info.get("results", None) is not None
    assert atoms.info["results"].get("calc0", None) is not None
    assert atoms.info["results"]["calc0"].get("magmom", None) is None
    atoms = SmartVasp(atoms)
    atoms.calc.results = {"magmom": mag - 2}
    atoms = prep_next_run(atoms, store_results=True)
    assert atoms.info.get("results", None) is not None
    assert atoms.info["results"].get("calc1", None) is not None
    assert atoms.info["results"]["calc0"].get("magmom", None) is None
    assert atoms.info["results"]["calc1"]["magmom"] == mag - 2
    assert decode(encode(atoms)) == atoms
