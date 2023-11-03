"""Common workflows for phonons"""
from __future__ import annotations

from typing import TYPE_CHECKING

import phonopy
from monty.dev import requires
from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.io.phonopy import get_phonopy_structure, get_pmg_structure

from quacc import subflow
from quacc.recipes.common.core import force_job

try:
    import phonopy
except ImportError:
    phonopy = None

if TYPE_CHECKING:
    from typing import TypedDict

    from ase.atoms import Atoms
    from numpy.typing import ArrayLike, NDArray
    from phonopy.structure.atoms import PhonopyAtoms

    from quacc.recipes.common.core import force_job

    class ThermalProperties(TypedDict):
        temperatures: NDArray
        free_energy: NDArray
        entropy: NDArray
        heat_capacity: NDArray

    class PhononSchema(TypedDict):
        phonon: phonopy.Phonopy
        thermal_properties: ThermalProperties


@requires(phonopy, "Phonopy must be installed. Run `pip install quacc[phonons]`")
def run_phonons(
    atoms: Atoms,
    supercell_matrix: ArrayLike = ((2, 0, 0), (0, 2, 0), (0, 0, 2)),
    atom_disp: float = 0.015,
    t_step: float = 10,
    t_max: float = 1000,
    t_min: float = 0,
) -> PhononSchema:
    """
    Calculate phonon properties.

    This module is adapted from `matcalc` (https://github.com/materialsvirtuallab/matcalc)

    Parameters
    ----------
    atoms
        Atoms object with calculator attached.
    calculator
        Calculator to use.
    supercell_matrix
        Supercell matrix to use. Defaults to 2x2x2 supercell.
    atom_disp
        Atomic displacement
    t_step
        Temperature step.
    t_max
        Max temperature.
    t_min
        Min temperature.

    Returns
    -------
    PhononSchema
        Dictionary of results
    """

    @subflow
    def _calc_phonons_distributed(atoms: Atoms) -> PhononSchema:
        calculator = atoms.calc
        structure = AseAtomsAdaptor().get_structure(atoms)

        phonopy_atoms = get_phonopy_structure(structure)
        phonon = phonopy.Phonopy(phonopy_atoms, supercell_matrix)
        phonon.generate_displacements(distance=atom_disp)
        supercells = phonon.supercells_with_displacements

        phonon.forces = [
            force_job(_get_atoms_from_phonopy(supercell), calculator)
            for supercell in supercells
            if supercell is not None
        ]
        phonon.produce_force_constants()
        phonon.run_mesh()
        phonon.run_thermal_properties(t_step=t_step, t_max=t_max, t_min=t_min)

        return {
            "phonon": phonon,
            "thermal_properties": phonon.get_thermal_properties_dict(),
        }

    return _calc_phonons_distributed(atoms)


def _get_atoms_from_phonopy(phonpy_atoms: PhonopyAtoms) -> Atoms:
    """
    Convert a phonopy atoms object to an ASE atoms object.

    Parameters
    ----------
    phonpy_atoms
        Phonopy atoms object

    Returns
    -------
    Atoms
        ASE atoms object
    """
    pmg_structure = get_pmg_structure(phonpy_atoms)
    return AseAtomsAdaptor().get_atoms(pmg_structure)
