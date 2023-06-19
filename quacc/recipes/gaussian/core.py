"""Core recipes for Gaussian"""
from __future__ import annotations

import multiprocessing

import covalent as ct
from ase.atoms import Atoms
from ase.calculators.gaussian import Gaussian

from quacc.schemas.cclib import summarize_run
from quacc.util.calc import run_calc
from quacc.util.dicts import remove_dict_empties

LOG_FILE = f"{Gaussian().label}.log"
GEOM_FILE = LOG_FILE


@ct.electron
def static_job(
    atoms: Atoms,
    charge: int | None = None,
    multiplicity: int | None = None,
    xc: str = "wb97x-d",
    basis: str = "def2-tzvp",
    write_molden: bool = True,
    calc_swaps: dict | None = None,
) -> dict:
    """
    Carry out a single-point calculation.

    Parameters
    ----------
    atoms
        Atoms object
    charge
        Charge of the system. If None, this is determined from the sum of
        `atoms.get_initial_charges().`
    multiplicity
        Multiplicity of the system. If None, this is determined from 1+ the sum
        of `atoms.get_initial_magnetic_moments()`.
    xc
        Exchange-correlation functional
    basis
        Basis set
    write_molden
        Whether to write a molden file for orbital visualization
    calc_swaps
        Dictionary of custom kwargs for the calculator.
            defaults = {
                "mem": "16GB",
                "chk": "Gaussian.chk",
                "nprocshared": multiprocessing.cpu_count(),
                "xc": xc,
                "basis": basis,
                "charge": charge or int(sum(atoms.get_initial_charges())),
                "mult": multiplicity or int(1 + sum(atoms.get_initial_magnetic_moments())),
                "sp": "",
                "scf": ["maxcycle=250", "xqc"],
                "integral": "ultrafine",
                "nosymmetry": "",
                "pop": "CM5",
                "gfinput": "" if write_molden else None,
                "ioplist": ["6/7=3", "2/9=2000"]
                if write_molden
                else ["2/9=2000"],  # see ASE issue #660
            }

    Returns
    -------
    dict
        Dictionary of results from `quacc.schemas.cclib.summarize_run`
    """

    calc_swaps = calc_swaps or {}

    charge = charge or int(atoms.get_initial_charges().sum())
    multiplicity = multiplicity or int(1 + atoms.get_initial_magnetic_moments().sum())
    defaults = {
        "mem": "16GB",
        "chk": "Gaussian.chk",
        "nprocshared": multiprocessing.cpu_count(),
        "xc": xc,
        "basis": basis,
        "charge": charge,
        "mult": multiplicity,
        "sp": "",
        "scf": ["maxcycle=250", "xqc"],
        "integral": "ultrafine",
        "nosymmetry": "",
        "pop": "CM5",
        "gfinput": "" if write_molden else None,
        "ioplist": ["6/7=3", "2/9=2000"]
        if write_molden
        else ["2/9=2000"],  # see ASE issue #660
    }
    flags = remove_dict_empties(defaults | calc_swaps)

    atoms.calc = Gaussian(**flags)
    atoms = run_calc(atoms, geom_file=GEOM_FILE)

    return summarize_run(
        atoms,
        LOG_FILE,
        additional_fields={"name": "Gaussian Static"},
    )


@ct.electron
def relax_job(
    atoms: Atoms,
    charge: int | None = None,
    multiplicity: int | None = None,
    xc: str = "wb97x-d",
    basis: str = "def2-tzvp",
    freq: bool = False,
    calc_swaps: dict | None = None,
) -> dict:
    """
    Carry out a geometry optimization.

    Parameters
    ----------
    atoms
        Atoms object
    charge
        Charge of the system. If None, this is determined from the sum of
        `atoms.get_initial_charges()`.
    multiplicity
        Multiplicity of the system. If None, this is determined from 1+ the sum
        of `atoms.get_initial_magnetic_moments()`.
    xc
        Exchange-correlation functional
    basis
        Basis set
    freq
        If a frequency calculation should be carried out.
    calc_swaps
        Dictionary of custom kwargs for the calculator.
            defaults = {
                "mem": "16GB",
                "chk": "Gaussian.chk",
                "nprocshared": multiprocessing.cpu_count(),
                "xc": xc,
                "basis": basis,
                "charge": charge or int(sum(atoms.get_initial_charges())),
                "mult": multiplicity or int(1 + sum(atoms.get_initial_magnetic_moments())),
                "opt": "",
                "pop": "CM5",
                "scf": ["maxcycle=250", "xqc"],
                "integral": "ultrafine",
                "nosymmetry": "",
                "freq": "" if freq else None,
                "ioplist": ["2/9=2000"],  # ASE issue #660
            }

    Returns
    -------
    dict
        Dictionary of results from `quacc.schemas.cclib.summarize_run`
    """

    calc_swaps = calc_swaps or {}

    charge = charge or int(atoms.get_initial_charges().sum())
    multiplicity = multiplicity or int(1 + atoms.get_initial_magnetic_moments().sum())

    defaults = {
        "mem": "16GB",
        "chk": "Gaussian.chk",
        "nprocshared": multiprocessing.cpu_count(),
        "xc": xc,
        "basis": basis,
        "charge": charge,
        "mult": multiplicity,
        "opt": "",
        "pop": "CM5",
        "scf": ["maxcycle=250", "xqc"],
        "integral": "ultrafine",
        "nosymmetry": "",
        "freq": "" if freq else None,
        "ioplist": ["2/9=2000"],  # ASE issue #660
    }
    flags = remove_dict_empties(defaults | calc_swaps)

    atoms.calc = Gaussian(**flags)
    atoms = run_calc(atoms, geom_file=GEOM_FILE)

    return summarize_run(
        atoms,
        LOG_FILE,
        additional_fields={"name": "Gaussian Relax"},
    )
