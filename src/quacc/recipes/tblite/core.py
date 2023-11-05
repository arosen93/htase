"""Core recipes for the tblite code."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ase.optimize import FIRE
from monty.dev import requires

from quacc import job
from quacc.builders.thermo import build_ideal_gas
from quacc.runners.ase import run_calc, run_opt, run_vib
from quacc.schemas.ase import summarize_opt_run, summarize_run, summarize_vib_and_thermo
from quacc.utils.dicts import merge_dicts

try:
    from tblite.ase import TBLite
except ImportError:
    TBLite = None

if TYPE_CHECKING:
    from typing import Any, Literal

    from ase import Atoms

    from quacc.runners.ase import VibKwargs
    from quacc.schemas._aliases.ase import OptSchema, RunSchema, VibThermoSchema


@job
@requires(TBLite, "tblite must be installed. Refer to the quacc documentation.")
def static_job(
    atoms: Atoms,
    method: Literal["GFN1-xTB", "GFN2-xTB", "IPEA1-xTB"] = "GFN2-xTB",
    **kwargs,
) -> RunSchema:
    """
    Carry out a single-point calculation.

    Parameters
    ----------
    atoms
        Atoms object
    method
        GFN1-xTB, GFN2-xTB, and IPEA1-xTB.
    **kwargs
        Custom kwargs for the TBLite calculator. Set a value to
        `None` to remove a pre-existing key entirely. For a list of available
        keys, refer to the `tblite.ase.TBLite` calculator.

        !!! Info "Calculator defaults"

            ```python
            {"method": method}
            ```
    Returns
    -------
    RunSchema
        Dictionary of results from [quacc.schemas.ase.summarize_run][]
    """

    defaults = {"method": method}
    flags = merge_dicts(defaults, kwargs)
    atoms.calc = TBLite(**flags)

    final_atoms = run_calc(atoms)
    return summarize_run(
        final_atoms,
        input_atoms=atoms,
        additional_fields={"name": "TBLite Static"},
    )


@job
@requires(TBLite, "tblite must be installed. Refer to the quacc documentation.")
def relax_job(
    atoms: Atoms,
    method: Literal["GFN1-xTB", "GFN2-xTB", "IPEA1-xTB"] = "GFN2-xTB",
    relax_cell: bool = False,
    opt_params: dict[str, Any] | None = None,
    **kwargs,
) -> OptSchema:
    """
    Relax a structure.

    Parameters
    ----------
    atoms
        Atoms object
    method
        GFN0-xTB, GFN1-xTB, GFN2-xTB.
    relax_cell
        Whether to relax the cell.
    opt_params
        Dictionary of custom kwargs for the optimization process. Set a value
        to `None` to remove a pre-existing key entirely. For a list of available
        keys, refer to [quacc.runners.ase.run_opt][].

        !!! Info "Optimizer defaults"

            ```python
            {"fmax": 0.01, "max_steps": 1000, "optimizer": FIRE}
            ```
    **kwargs
        Custom kwargs for the tblite calculator. Set a value to
        `None` to remove a pre-existing key entirely. For a list of available
        keys, refer to the `tblite.ase.TBLite` calculator.

        !!! Info "Calculator defaults"

            ```python
            {"method": method}
            ```
    Returns
    -------
    OptSchema
        Dictionary of results from [quacc.schemas.ase.summarize_opt_run][]
    """

    defaults = {"method": method}
    flags = merge_dicts(defaults, kwargs)
    atoms.calc = TBLite(**flags)

    opt_defaults = {"fmax": 0.01, "max_steps": 1000, "optimizer": FIRE}
    opt_flags = merge_dicts(opt_defaults, opt_params)

    dyn = run_opt(atoms, relax_cell=relax_cell, **opt_flags)

    return summarize_opt_run(dyn, additional_fields={"name": "TBLite Relax"})


@job
@requires(TBLite, "tblite must be installed. Refer to the quacc documentation.")
def freq_job(
    atoms: Atoms,
    method: Literal["GFN1-xTB", "GFN2-xTB", "IPEA1-xTB"] = "GFN2-xTB",
    energy: float = 0.0,
    temperature: float = 298.15,
    pressure: float = 1.0,
    vib_kwargs: VibKwargs | None = None,
    **kwargs,
) -> VibThermoSchema:
    """
    Run a frequency job and calculate thermochemistry.

    !!! Info "Calculator defaults"

        ```python
        {"method": method}
        ```

    Parameters
    ----------
    atoms
        Atoms object
    method
        GFN0-xTB, GFN1-xTB, GFN2-xTB, GFN-FF.
    energy
        Potential energy in eV. If 0, then the output is just the correction.
    temperature
        Temperature in Kelvins.
    pressure
        Pressure in bar.
    vib_kwargs
        Dictionary of kwargs for the `ase.vibrations.Vibrations` class.
    **kwargs
        Custom kwargs for the tblite calculator. Set a value to
        `None` to remove a pre-existing key entirely. For a list of available
        keys, refer to the `tblite.ase.TBLite` calculator.

    Returns
    -------
    VibThermoSchema
        Dictionary of results from [quacc.schemas.ase.summarize_vib_and_thermo][]
    """
    vib_kwargs = vib_kwargs or {}

    defaults = {"method": method}
    flags = merge_dicts(defaults, kwargs)
    atoms.calc = TBLite(**flags)

    vibrations = run_vib(atoms, vib_kwargs=vib_kwargs)
    igt = build_ideal_gas(atoms, vibrations.get_frequencies(), energy=energy)

    return summarize_vib_and_thermo(
        vibrations,
        igt,
        temperature=temperature,
        pressure=pressure,
        additional_fields={"name": "TBLite Frequency and Thermo"},
    )
