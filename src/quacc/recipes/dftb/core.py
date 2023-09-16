"""Core recipes for DFTB+"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ase.calculators.dftb import Dftb

from quacc import job
from quacc.schemas import fetch_atoms
from quacc.schemas.ase import summarize_run
from quacc.utils.calc import run_calc
from quacc.utils.dicts import merge_dicts
from quacc.utils.files import check_logfile

if TYPE_CHECKING:
    from typing import Literal

    from ase import Atoms

    from quacc.schemas.ase import RunSchema

LOG_FILE = "dftb.out"
GEOM_FILE = "geo_end.gen"


@job
def static_job(
    atoms: Atoms | dict,
    method: Literal["GFN1-xTB", "GFN2-xTB", "DFTB"] = "GFN2-xTB",
    kpts: tuple | list[tuple] | dict | None = None,
    calc_swaps: dict | None = None,
    copy_files: list[str] | None = None,
) -> RunSchema:
    """
    Carry out a single-point calculation.

    Parameters
    ----------
    atoms
        Atoms object or a dictionary with the key "atoms" and an Atoms object as
        the value
    method
        Method to use.
    kpts
        k-point grid to use. Defaults to None for molecules and (1, 1, 1) for
        solids.
    calc_swaps
        Dictionary of custom kwargs for the calculator.

        ???+ Note

             Overrides the following defaults:

            ```python
            {
                "Hamiltonian_": "xTB" if "xtb" in method.lower()
                else "DFTB", "Hamiltonian_Method": method if "xtb" in method.lower()
                else None, "kpts": kpts or ((1, 1, 1) if atoms.pbc.any() else None)
            }
            ```
    copy_files
        Files to copy to the runtime directory.

    Returns
    -------
    RunSchema
        Dictionary of results, specified in [quacc.schemas.ase.summarize_run][]
    """

    defaults = {
        "Hamiltonian_": "xTB" if "xtb" in method.lower() else "DFTB",
        "Hamiltonian_Method": method if "xtb" in method.lower() else None,
        "kpts": kpts or ((1, 1, 1) if atoms.pbc.any() else None),
    }

    summary = _base_job(
        atoms,
        flags=merge_dicts(defaults, calc_swaps),
        copy_files=copy_files,
        additional_fields={"name": "DFTB+ Static"},
    )

    msg = "SCC is not converged"
    if check_logfile(LOG_FILE, msg):
        raise ValueError(msg)

    return summary


@job
def relax_job(
    atoms: Atoms | dict,
    method: Literal["GFN1-xTB", "GFN2-xTB", "DFTB"] = "GFN2-xTB",
    kpts: tuple | list[tuple] | dict | None = None,
    relax_cell: bool = False,
    calc_swaps: dict | None = None,
    copy_files: list[str] | None = None,
) -> RunSchema:
    """
    Carry out a structure relaxation.

    Parameters
    ----------
    atoms
        Atoms object or a dictionary with the key "atoms" and an Atoms object as
        the value
    method
        Method to use.
    kpts
        k-point grid to use. Defaults to None for molecules and (1, 1, 1) for
        solids.
    relax_cell
        Whether to relax the unit cell shape/volume in addition to the
        positions.
    calc_swaps
        Dictionary of custom kwargs for the calculator.

        ???+ Note

             Overrides the following defaults:

            ```python
            {
                "Hamiltonian_": "xTB" if "xtb" in method.lower() else "DFTB",
                "Hamiltonian_Method": method if "xtb" in method.lower() else None,
                "kpts": kpts or ((1, 1, 1) if atoms.pbc.any() else None),
                "Driver_": "GeometryOptimization",
                "Driver_LatticeOpt": "Yes" if relax_cell else "No",
                "Driver_AppendGeometries": "Yes",
                "Driver_MaxSteps": 2000,
            }
            ```
    copy_files
        Files to copy to the runtime directory.

    Returns
    -------
    RunSchema
        Dictionary of results, specified in [quacc.schemas.ase.summarize_run][]
    """

    defaults = {
        "Hamiltonian_": "xTB" if "xtb" in method.lower() else "DFTB",
        "Hamiltonian_Method": method if "xtb" in method.lower() else None,
        "kpts": kpts or ((1, 1, 1) if atoms.pbc.any() else None),
        "Driver_": "GeometryOptimization",
        "Driver_LatticeOpt": "Yes" if relax_cell else "No",
        "Driver_AppendGeometries": "Yes",
        "Driver_MaxSteps": 2000,
    }

    summary = _base_job(
        atoms,
        flags=merge_dicts(defaults, calc_swaps),
        additional_fields={"name": "DFTB+ Relax"},
        copy_files=copy_files,
    )

    msg = "Geometry converged"
    if check_logfile(LOG_FILE, msg):
        raise ValueError(msg)

    return summary


def _base_job(
    atoms: Atoms | dict,
    flags: dict | None = None,
    additional_fields: dict | None = None,
    copy_files: list[str] | None = None,
) -> RunSchema:
    """
    Base job function used for various DFTB+ recipes.

    Parameters
    ----------
    atoms
        Atoms object or a dictionary with the key "atoms" and an Atoms object as
        the value
    flags
        The calculator flags to use.
    additional_fields
        Any `additional_fields` to set in the summary.
    copy_files
        Files to copy to the runtime directory.

    Returns
    -------
    RunSchema
        Dictionary of results, specified in [quacc.schemas.ase.summarize_run][]
    """
    atoms = fetch_atoms(atoms)
    flags = flags or {}

    atoms.calc = Dftb(**flags)
    final_atoms = run_calc(atoms, geom_file=GEOM_FILE, copy_files=copy_files)

    return summarize_run(
        final_atoms,
        input_atoms=atoms,
        additional_fields=additional_fields,
    )
