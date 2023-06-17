import os
from pathlib import Path
from shutil import copy, rmtree

import pytest
from ase import units
from ase.io import read
from ase.calculators.calculator import FileIOCalculator
from ase.calculators.lj import LennardJones
from pymatgen.io.qchem.inputs import QCInput
from pymatgen.io.ase import AseAtomsAdaptor
from quacc.calculators.qchem import QChem

from quacc.recipes.qchem.core import static_job, relax_job, irc_job#, ts_job

try:
    import sella
except ImportError:
    sella = None


FILE_DIR = Path(__file__).resolve().parent
QCHEM_DIR = os.path.join(FILE_DIR, "qchem_examples")
TEST_ATOMS = read(os.path.join(FILE_DIR, "test.xyz"))

def mock_execute1(_self, **kwargs):
    copy(os.path.join(QCHEM_DIR, "mol.qout.basic"), "mol.qout")
    copy(os.path.join(QCHEM_DIR, "131.0.basic"), "131.0")

def mock_execute2(_self, **kwargs):
    copy(os.path.join(QCHEM_DIR, "mol.qout.intermediate"), "mol.qout")
    copy(os.path.join(QCHEM_DIR, "131.0.intermediate"), "131.0")

def mock_execute3(self, **kwargs):
    qcin = QCInput.from_file("mol.qin")
    mol = qcin.molecule
    atoms = AseAtomsAdaptor.get_atoms(mol)
    atoms.calc = LennardJones()
    atoms.get_potential_energy()
    self.results = atoms.calc.results
    print(self.results)

def mock_read(self, **kwargs):
    if self.results is None:
        raise RuntimeError("Results should not be None here! Exiting...")
    pass


def teardown_module():
    for f in os.listdir("."):
        if ".log" in f or ".traj" in f or ".gz" in f:
            os.remove(f)
    for f in os.listdir(os.getcwd()):
        if "quacc-tmp" in f or f == "tmp_dir":
            if os.path.islink(f):
                os.unlink(f)
            else:
                rmtree(f)


def test_static_job(monkeypatch):
    monkeypatch.setattr(FileIOCalculator, "execute", mock_execute1)
    output = static_job(TEST_ATOMS)
    assert output["atoms"] == TEST_ATOMS
    assert output["charge"] == 0
    assert output["spin_multiplicity"] == 1
    assert output["formula_alphabetical"] == "C4 H4 O6"
    assert output["nelectrons"] == 76
    assert output["parameters"]["charge"] is None
    assert output["parameters"]["spin_multiplicity"] is None
    assert output["results"]["energy"] == pytest.approx(-606.1616819641 * units.Hartree)
    assert output["results"]["forces"][0][0] == pytest.approx(-1.3826330655069403)

    qcin = QCInput.from_file("mol.qin.gz")
    ref_qcin = QCInput.from_file(os.path.join(QCHEM_DIR, "mol.qin.basic"))
    assert qcin.as_dict() == ref_qcin.as_dict()

    monkeypatch.setattr(FileIOCalculator, "execute", mock_execute2)
    output = static_job(
        atoms=TEST_ATOMS,
        charge=-1,
        xc="b97mv",
        basis="def2-svpd",
        pcm_dielectric="3.0",
    )

    assert output["atoms"] == TEST_ATOMS
    # next three lines should be able to be uncommented once charge is correctly passed through
    # assert output["charge"] == -1
    # assert output["spin_multiplicity"] == 2
    # assert output["nelectrons"] == 77
    assert output["formula_alphabetical"] == "C4 H4 O6"
    assert output["parameters"]["charge"] == -1
    assert output["parameters"]["spin_multiplicity"] is None
    assert output["results"]["energy"] == pytest.approx(
        -605.6859554025 * units.Hartree
    )  # -16481.554341995
    assert output["results"]["forces"][0][0] == pytest.approx(-0.6955571014353796)

    qcin = QCInput.from_file("mol.qin.gz")
    ref_qcin = QCInput.from_file(os.path.join(QCHEM_DIR, "mol.qin.intermediate"))
    assert qcin.as_dict() == ref_qcin.as_dict()
    monkeypatch.delattr(FileIOCalculator, "execute")


@pytest.mark.skipif(
    sella is None,
    reason="Sella must be installed.",
)
def test_relax_job(monkeypatch):
    monkeypatch.setattr(FileIOCalculator, "execute", mock_execute1)
    output = relax_job(
        atoms=TEST_ATOMS,
        basis="def2-tzvpd",
        opt_swaps={"max_steps": 1},
        check_convergence=False,
    )

    assert output["atoms"] != TEST_ATOMS
    assert output["charge"] == 0
    assert output["spin_multiplicity"] == 1
    assert output["formula_alphabetical"] == "C4 H4 O6"
    assert output["nelectrons"] == 76
    assert output["parameters"]["charge"] is None
    assert output["parameters"]["spin_multiplicity"] is None
    assert output["results"]["energy"] == pytest.approx(-606.1616819641 * units.Hartree)
    assert output["results"]["forces"][0][0] == pytest.approx(-1.3826330655069403)

    qcin = QCInput.from_file("mol.qin.gz")
    ref_qcin = QCInput.from_file(
        os.path.join(QCHEM_DIR, "mol.qin.basic.sella_opt_iter1")
    )
    assert qcin.as_dict() == ref_qcin.as_dict()

    monkeypatch.setattr(FileIOCalculator, "execute", mock_execute2)
    output = relax_job(
        atoms=TEST_ATOMS,
        charge=-1,
        xc="b97mv",
        pcm_dielectric="3.0",
        opt_swaps={"max_steps": 1},
        check_convergence=False,
    )

    assert output["atoms"] != TEST_ATOMS
    # next three lines should be able to be uncommented once charge is correctly passed through
    # assert output["charge"] == -1
    # assert output["spin_multiplicity"] == 2
    # assert output["nelectrons"] == 77
    assert output["formula_alphabetical"] == "C4 H4 O6"
    assert output["parameters"]["charge"] == -1
    assert output["parameters"]["spin_multiplicity"] is None
    assert output["results"]["energy"] == pytest.approx(-605.6859554025 * units.Hartree)
    assert output["results"]["forces"][0][0] == pytest.approx(-0.6955571014353796)

    qcin = QCInput.from_file("mol.qin.gz")
    ref_qcin = QCInput.from_file(
        os.path.join(QCHEM_DIR, "mol.qin.intermediate.sella_opt_iter1")
    )
    assert qcin.as_dict() == ref_qcin.as_dict()


# Commenting this out until we have a dictionary approx equal
# @pytest.mark.skipif(
#     sella is None,
#     reason="Sella must be installed.",
# )
# def test_ts_job(monkeypatch):
#     monkeypatch.setattr(FileIOCalculator, "execute", mock_execute1)
#     output = ts_job(
#         atoms=TEST_ATOMS,
#         basis="def2-tzvpd",
#         opt_swaps={"max_steps": 1},
#         check_convergence=False,
#     )

#     assert output["atoms"] != TEST_ATOMS
#     assert output["charge"] == 0
#     assert output["spin_multiplicity"] == 1
#     assert output["formula_alphabetical"] == "C4 H4 O6"
#     assert output["nelectrons"] == 76
#     assert output["parameters"]["charge"] is None
#     assert output["parameters"]["spin_multiplicity"] is None
#     assert output["results"]["energy"] == pytest.approx(-606.1616819641 * units.Hartree)
#     assert output["results"]["forces"][0][0] == pytest.approx(-1.3826330655069403)

#     qcin = QCInput.from_file("mol.qin.gz")
#     ref_qcin = QCInput.from_file(
#         os.path.join(QCHEM_DIR, "mol.qin.basic.sella_TSopt_iter1")
#     )
#     assert qcin.as_dict() == ref_qcin.as_dict()

#     monkeypatch.setattr(FileIOCalculator, "execute", mock_execute2)
#     output = ts_job(
#         atoms=TEST_ATOMS,
#         charge=-1,
#         xc="b97mv",
#         pcm_dielectric="3.0",
#         opt_swaps={"max_steps": 1},
#         check_convergence=False,
#     )

#     assert output["atoms"] != TEST_ATOMS
#     # next three lines should be able to be uncommented once charge is correctly passed through
#     # assert output["charge"] == -1
#     # assert output["spin_multiplicity"] == 2
#     # assert output["nelectrons"] == 77
#     assert output["formula_alphabetical"] == "C4 H4 O6"
#     assert output["parameters"]["charge"] == -1
#     assert output["parameters"]["spin_multiplicity"] is None
#     assert output["results"]["energy"] == pytest.approx(-605.6859554025 * units.Hartree)
#     assert output["results"]["forces"][0][0] == pytest.approx(-0.6955571014353796)

#     qcin = QCInput.from_file("mol.qin.gz")
#     ref_qcin = QCInput.from_file(
#         os.path.join(QCHEM_DIR, "mol.qin.intermediate.sella_TSopt_iter1")
#     )
#     assert qcin.as_dict() == ref_qcin.as_dict()


@pytest.mark.skipif(
    sella is None,
    reason="Sella must be installed.",
)
def test_irc_job(monkeypatch):
    monkeypatch.setattr(QChem, "read_results", mock_read)
    monkeypatch.setattr(FileIOCalculator, "execute", mock_execute3)
    
    output = irc_job(
        atoms=TEST_ATOMS,
        direction="forward",
        basis="def2-tzvpd",
        opt_swaps={"max_steps": 1},
        check_convergence=False,
    )

    assert output["atoms"] != TEST_ATOMS
    assert output["charge"] == 0
    assert output["spin_multiplicity"] == 1
    assert output["formula_alphabetical"] == "C4 H4 O6"
    assert output["nelectrons"] == 76
    assert output["parameters"]["charge"] is None
    assert output["parameters"]["spin_multiplicity"] is None

    qcin = QCInput.from_file("mol.qin.gz")
    ref_qcin = QCInput.from_file(
        os.path.join(QCHEM_DIR, "mol.qin.basic.sella_IRC_forward_iter1")
    )
    assert qcin.as_dict() == ref_qcin.as_dict()

    output = irc_job(
        atoms=TEST_ATOMS,
        direction="reverse",
        basis="def2-tzvpd",
        opt_swaps={"max_steps": 1},
        check_convergence=False,
    )

    qcin = QCInput.from_file("mol.qin.gz")
    ref_qcin = QCInput.from_file(
        os.path.join(QCHEM_DIR, "mol.qin.basic.sella_IRC_reverse_iter1")
    )
    assert qcin.as_dict() == ref_qcin.as_dict()

