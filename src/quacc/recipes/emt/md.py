"""
Molecular Dynamics recipes for EMT.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ase.calculators.emt import EMT
from ase.md.verlet import VelocityVerlet
from ase.units import bar, fs

from quacc import Remove, job
from quacc.runners.ase import Runner
from quacc.schemas.ase import summarize_md_run
from quacc.utils.dicts import recursive_dict_merge

if TYPE_CHECKING:
    from ase.atoms import Atoms
    from ase.md.md import MolecularDynamics

    from quacc.runners.ase import MDParams
    from quacc.schemas._aliases.ase import DynSchema
    from quacc.utils.files import Filenames, SourceDirectory


@job
def md_job(
    atoms: Atoms,
    dynamics: MolecularDynamics = VelocityVerlet,
    steps: int = 1000,
    timestep_fs: float = 1.0,
    temperature_K: float | None = None,
    pressure_bar: float | None = None,
    initial_temperature_K: float | None = None,
    md_params: MDParams | None = None,
    copy_files: SourceDirectory | dict[SourceDirectory, Filenames] | None = None,
    **calc_kwargs,
) -> DynSchema:
    """
    Carry out a Molecular Dynamics calculation.

    Parameters
    ----------
    atoms
        Atoms object
    dynamics
        ASE `MolecularDynamics` class to use, from `ase.md.md.MolecularDynamics`.
    steps
        Number of MD steps to run.
    timestep_fs
        Time step in fs.
    temperature_K
        Temperature in K, if applicable for the given ensemble.
    pressure_bar
        Pressure in bar, if applicable for the given ensemble.
    initial_temperature_K
        Initial temperature (in K) to specify via a Maxwell-Boltzmann distribution.
    md_params
        Dictionary of custom kwargs for the MD run. For a list of available
        keys, refer to [quacc.runners.ase.Runner.run_md][].
    copy_files
        Files to copy (and decompress) from source to the runtime directory.
    **calc_kwargs
        Custom kwargs for the EMT calculator. Set a value to
        `quacc.Remove` to remove a pre-existing key entirely. For a list of available
        keys, refer to the `ase.calculators.emt.EMT` calculator.

    Returns
    -------
    DynSchema
        Dictionary of results, specified in [quacc.schemas.ase.summarize_md_run][].
        See the type-hint for the data structure.
    """
    md_defaults = {
        "steps": steps,
        "dynamics_kwargs": {
            "timestep": timestep_fs * fs,
            "temperature_K": temperature_K if temperature_K else Remove,
            "pressure_au": pressure_bar * bar if pressure_bar else Remove,
        },
        "maxwell_boltzmann_kwargs": {"temperature_K": initial_temperature_K}
        if initial_temperature_K
        else None,
        "set_com_stationary": bool(initial_temperature_K),
        "set_zero_rotation": bool(initial_temperature_K),
    }
    md_params = recursive_dict_merge(md_defaults, md_params)

    calc = EMT(**calc_kwargs)
    dyn = Runner(atoms, calc, copy_files=copy_files).run_md(dynamics, **md_params)

    return summarize_md_run(dyn, additional_fields={"name": "EMT MD"})
