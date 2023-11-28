"""Core recipes for DFTB+"""
from __future__ import annotations

from typing import TYPE_CHECKING

from quacc import job
from quacc.recipes.dftb._base import base_fn
from quacc.utils.dicts import merge_dicts

if TYPE_CHECKING:
    from typing import Literal

    from ase import Atoms

    from quacc.schemas._aliases.ase import RunSchema

_BASE_CALC_DEFAULTS = {
    "Analysis_CalculateForces": "Yes",
    "Hamiltonian_MaxSccIterations": 200,
    "Options_WriteResultsTag": "Yes",
}


@job
def static_job(
    atoms: Atoms,
    method: Literal["GFN1-xTB", "GFN2-xTB", "DFTB"] = "GFN2-xTB",
    kpts: tuple | list[tuple] | dict | None = None,
    **calc_kwargs,
) -> RunSchema:
    """
    Carry out a single-point calculation.

    Parameters
    ----------
    atoms
        Atoms object
    method
        Method to use.
    kpts
        k-point grid to use.
    **calc_kwargs
        Custom kwargs for the calculator that would override the
        calculator defaults. Set a value to `None` to remove a pre-existing key
        entirely. For a list of available keys, refer to the
        `ase.calculators.dftb.Dftb` calculator.

    Returns
    -------
    RunSchema
        Dictionary of results, specified in [quacc.schemas.ase.summarize_run][]
    """

    calc_defaults = merge_dicts(
        _BASE_CALC_DEFAULTS,
        {
            "Hamiltonian_": "xTB" if "xtb" in method.lower() else "DFTB",
            "Hamiltonian_Method": method if "xtb" in method.lower() else None,
            "kpts": kpts or ((1, 1, 1) if atoms.pbc.any() else None),
        },
    )

    return base_fn(
        atoms,
        calc_defaults=calc_defaults,
        calc_swaps=calc_kwargs,
        additional_fields={"name": "DFTB+ Static"},
    )


@job
def relax_job(
    atoms: Atoms,
    method: Literal["GFN1-xTB", "GFN2-xTB", "DFTB"] = "GFN2-xTB",
    kpts: tuple | list[tuple] | dict | None = None,
    relax_cell: bool = False,
    **calc_kwargs,
) -> RunSchema:
    """
    Carry out a structure relaxation.

    Parameters
    ----------
    atoms
        Atoms object
    method
        Method to use.
    kpts
        k-point grid to use.
    relax_cell
        Whether to relax the unit cell shape/volume in addition to the
        positions.
    **calc_kwargs
        Custom kwargs for the calculator that would override the
        calculator defaults. Set a value to `None` to remove a pre-existing key
        entirely. For a list of available keys, refer to the
        `ase.calculators.dftb.Dftb` calculator.

    Returns
    -------
    RunSchema
        Dictionary of results, specified in [quacc.schemas.ase.summarize_run][]
    """

    calc_defaults = merge_dicts(
        _BASE_CALC_DEFAULTS,
        {
            "Driver_": "GeometryOptimization",
            "Driver_LatticeOpt": "Yes" if relax_cell else "No",
            "Driver_AppendGeometries": "Yes",
            "Driver_MaxSteps": 2000,
            "Hamiltonian_": "xTB" if "xtb" in method.lower() else "DFTB",
            "Hamiltonian_Method": method if "xtb" in method.lower() else None,
            "kpts": kpts or ((1, 1, 1) if atoms.pbc.any() else None),
        },
    )

    return base_fn(
        atoms,
        calc_defaults=calc_defaults,
        calc_swaps=calc_kwargs,
        additional_fields={"name": "DFTB+ Relax"},
    )
