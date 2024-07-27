"""Core recipes for the tblite code."""

from __future__ import annotations

from importlib.util import find_spec
from typing import TYPE_CHECKING

from monty.dev import requires

from quacc import job
from quacc.runners.ase import Runner
from quacc.schemas.ase import Summarize
from quacc.utils.dicts import recursive_dict_merge

has_tblite = bool(find_spec("tblite"))
if has_tblite:
    from tblite.ase import TBLite

if TYPE_CHECKING:
    from typing import Literal

    from ase.atoms import Atoms

    from quacc.types import OptParams, OptSchema, RunSchema, VibKwargs, VibThermoSchema


@job
@requires(has_tblite, "tblite must be installed. Refer to the quacc documentation.")
def static_job(
    atoms: Atoms,
    method: Literal["GFN1-xTB", "GFN2-xTB", "IPEA1-xTB"] = "GFN2-xTB",
    **calc_kwargs,
) -> RunSchema:
    """
    Carry out a single-point calculation.

    Parameters
    ----------
    atoms
        Atoms object
    method
        xTB method to use
    **calc_kwargs
        Custom kwargs for the TBLite calculator. Set a value to
        `quacc.Remove` to remove a pre-existing key entirely. For a list of available
        keys, refer to the `tblite.ase.TBLite` calculator

    Returns
    -------
    RunSchema
        Dictionary of results from [quacc.schemas.ase.Summarize.run][].
        See the type-hint for the data structure.
    """
    calc_defaults = {"method": method}
    calc_flags = recursive_dict_merge(calc_defaults, calc_kwargs)
    calc = TBLite(**calc_flags)

    final_atoms = Runner(atoms, calc).run_calc()
    return Summarize(additional_fields={"name": "TBLite Static"}).run(
        final_atoms, atoms
    )


@job
@requires(has_tblite, "tblite must be installed. Refer to the quacc documentation.")
def relax_job(
    atoms: Atoms,
    method: Literal["GFN1-xTB", "GFN2-xTB", "IPEA1-xTB"] = "GFN2-xTB",
    relax_cell: bool = False,
    opt_params: OptParams | None = None,
    **calc_kwargs,
) -> OptSchema:
    """
    Relax a structure.

    Parameters
    ----------
    atoms
        Atoms object
    method
        xTB method to use
    relax_cell
        Whether to relax the cell.
    opt_params
        Dictionary of custom kwargs for the optimization process. For a list
        of available keys, refer to [quacc.runners.ase.Runner.run_opt][].
    **calc_kwargs
        Custom kwargs for the tblite calculator. Set a value to
        `quacc.Remove` to remove a pre-existing key entirely. For a list of available
        keys, refer to the `tblite.ase.TBLite` calculator.

    Returns
    -------
    OptSchema
        Dictionary of results from [quacc.schemas.ase.Summarize.opt][].
        See the type-hint for the data structure.
    """
    opt_params = opt_params or {}
    calc_defaults = {"method": method}
    calc_flags = recursive_dict_merge(calc_defaults, calc_kwargs)
    calc = TBLite(**calc_flags)
    dyn = Runner(atoms, calc).run_opt(relax_cell=relax_cell, **opt_params)

    return Summarize(additional_fields={"name": "TBLite Relax"}).opt(dyn)


@job
@requires(has_tblite, "tblite must be installed. Refer to the quacc documentation.")
def freq_job(
    atoms: Atoms,
    method: Literal["GFN1-xTB", "GFN2-xTB", "IPEA1-xTB"] = "GFN2-xTB",
    energy: float = 0.0,
    temperature: float = 298.15,
    pressure: float = 1.0,
    vib_kwargs: VibKwargs | None = None,
    **calc_kwargs,
) -> VibThermoSchema:
    """
    Run a frequency job and calculate thermochemistry.

    Parameters
    ----------
    atoms
        Atoms object
    method
        xTB method to use
    energy
        Potential energy in eV. If 0, then the output is just the correction.
    temperature
        Temperature in Kelvins.
    pressure
        Pressure in bar.
    vib_kwargs
        Dictionary of kwargs for [quacc.runners.ase.Runner.run_vib][].
    **calc_kwargs
        Custom kwargs for the tblite calculator. Set a value to
        `quacc.Remove` to remove a pre-existing key entirely. For a list of available
        keys, refer to the `tblite.ase.TBLite` calculator.

    Returns
    -------
    VibThermoSchema
        Dictionary of results from [quacc.schemas.thermo.summarize_vib_and_thermo][].
        See the type-hint for the data structure.
    """
    vib_kwargs = vib_kwargs or {}

    calc_defaults = {"method": method}
    calc_flags = recursive_dict_merge(calc_defaults, calc_kwargs)
    calc = TBLite(**calc_flags)

    vib = Runner(atoms, calc).run_vib(vib_kwargs=vib_kwargs)
    return Summarize(additional_fields={"name": "TBLite Frequency and Thermo"}).vib(
        vib,
        thermo_method="ideal_gas",
        energy=energy,
        temperature=temperature,
        pressure=pressure,
    )
