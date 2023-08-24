"""Core recipes for VASP"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from quacc import job
from quacc.calculators.vasp import Vasp
from quacc.schemas.atoms import fetch_atoms
from quacc.schemas.vasp import summarize_run
from quacc.util.calc import run_calc
from quacc.util.dicts import merge_dicts

if TYPE_CHECKING:
    from ase import Atoms

    from quacc.schemas.vasp import VaspSchema


@job
def static_job(
    atoms: Atoms | dict,
    preset: str | None = None,
    calc_swaps: dict | None = None,
    copy_files: list[str] | None = None,
) -> VaspSchema:
    """
    Carry out a single-point calculation.

    Parameters
    ----------
    atoms
        Atoms object or a dictionary with the key "atoms" and an Atoms object as the value
    preset
        Preset to use.
    calc_swaps
        Dictionary of custom kwargs for the calculator.
    copy_files
        Absolute paths to files to copy to the runtime directory.

    Returns
    -------
    VaspSchema
        Dictionary of results from quacc.schemas.vasp.summarize_run
    """
    atoms = fetch_atoms(atoms)
    calc_swaps = calc_swaps or {}

    defaults = {
        "ismear": -5,
        "laechg": True,
        "lcharg": True,
        "lwave": True,
        "nedos": 5001,
        "nsw": 0,
    }
    flags = merge_dicts(defaults, calc_swaps)

    atoms.calc = Vasp(atoms, preset=preset, **flags)
    atoms = run_calc(atoms, copy_files=copy_files)

    return summarize_run(atoms, additional_fields={"name": "VASP Static"})


@job
def relax_job(
    atoms: Atoms | dict,
    preset: str | None = None,
    relax_cell: bool = True,
    calc_swaps: dict | None = None,
    copy_files: list[str] | None = None,
) -> VaspSchema:
    """
    Relax a structure.

    Parameters
    ----------
    atoms
        Atoms object or a dictionary with the key "atoms" and an Atoms object as the value
    preset
        Preset to use.
    relax_cell
        True if a volume relaxation (ISIF = 3) should be performed.
        False if only the positions (ISIF = 2) should be updated.
    calc_swaps
        Dictionary of custom kwargs for the calculator.
    copy_files
        Absolute paths to files to copy to the runtime directory.

    Returns
    -------
    VaspSchema
        Dictionary of results from quacc.schemas.vasp.summarize_run
    """
    atoms = fetch_atoms(atoms)
    calc_swaps = calc_swaps or {}

    defaults = {
        "ediffg": -0.02,
        "isif": 3 if relax_cell else 2,
        "ibrion": 2,
        "isym": 0,
        "lcharg": False,
        "lwave": False,
        "nsw": 200,
    }
    flags = merge_dicts(defaults, calc_swaps)

    atoms.calc = Vasp(atoms, preset=preset, **flags)
    atoms = run_calc(atoms, copy_files=copy_files)

    return summarize_run(atoms, additional_fields={"name": "VASP Relax"})


@job
def double_relax_job(
    atoms: Atoms | dict,
    preset: str | None = None,
    relax_cell: bool = True,
    calc_swaps1: dict | None = None,
    calc_swaps2: dict | None = None,
    copy_files: list[str] | None = None,
) -> dict[Literal["relax1", "relax2"], VaspSchema]:
    """
    Double-relax a structure. This is particularly useful for a few reasons:

    1. To carry out a cheaper pre-relaxation before the high-quality run.

    2. To carry out a GGA calculation before a meta-GGA or hybrid calculation
    that requires the GGA wavefunction.

    3. To carry out volume relaxations where large changes in volume
    can require a second relaxation to resolve forces.

    Parameters
    ----------
    atoms
        Atoms object or a dictionary with the key "atoms" and an Atoms object as the value
    preset
        Preset to use.
    relax_cell
        True if a volume relaxation (ISIF = 3) should be performed.
        False if only the positions (ISIF = 2) should be updated.
    calc_swaps1
        Dictionary of custom kwargs for the first relaxation.
    calc_swaps2
        Dictionary of custom kwargs for the second relaxation.
    copy_files
        Absolute paths to files to copy to the (first) runtime directory.

    Returns
    -------
    {"relax1": VaspSchema, "relax2": VaspSchema}
        Dictionaries of the type quacc.schemas.vasp.summarize_run.
    """
    atoms = fetch_atoms(atoms)
    calc_swaps1 = calc_swaps1 or {}
    calc_swaps2 = calc_swaps2 or {}

    # Run first relaxation
    summary1 = relax_job.original_func(
        atoms,
        preset=preset,
        relax_cell=relax_cell,
        calc_swaps=calc_swaps1,
        copy_files=copy_files,
    )

    # Run second relaxation
    summary2 = relax_job.original_func(
        summary1,
        preset=preset,
        relax_cell=relax_cell,
        calc_swaps=calc_swaps2,
        copy_files=["WAVECAR"],
    )

    return {"relax1": summary1, "relax2": summary2}
