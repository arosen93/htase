"""
Core recipes for the NewtonNet code
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import covalent as ct
import numpy as np
from ase.atoms import Atoms
from ase.units import _c, fs
from covalent._workflow.electron import Electron

from quacc import SETTINGS
from quacc.schemas.ase import summarize_opt_run, summarize_thermo_run
from quacc.util.calc import run_ase_opt
from quacc.util.thermo import ideal_gas

try:
    from newtonnet.utils.ase_interface import MLAseCalculator as NewtonNet
except ImportError:
    NewtonNet = "NewtonNet is not installed. Try pip install quacc[newtonnet]"


@ct.electron
def relax_job(
    atoms: Atoms,
    fmax: float = 0.01,
    max_steps: int = 1000,
    optimizer: str = "sella",
    newtonnet_kwargs: dict | None = None,
    opt_kwargs: dict | None = None,
) -> dict:
    """
    TODO: docstring
    """
    newtonnet_kwargs = newtonnet_kwargs or {}
    opt_kwargs = opt_kwargs or {}

    # Define calculator
    mlcalculator = NewtonNet(
        model_path=SETTINGS.NEWTONNET_MODEL_PATH,
        config_path=SETTINGS.NEWTONNET_CONFIG_PATH,
        **newtonnet_kwargs,
    )
    atoms.calc = mlcalculator

    opt_kwargs["order"] = 0

    dyn = run_ase_opt(
        atoms,
        fmax=fmax,
        max_steps=max_steps,
        optimizer=optimizer,
        opt_kwargs=opt_kwargs,
    )
    return summarize_opt_run(dyn, additional_fields={"name": "NewtonNet Relax"})


@ct.electron
def ts_job(
    atoms: Atoms,
    fmax: float = 0.01,
    max_steps: int = 1000,
    optimizer: str = "sella",
    use_custom_hessian: bool = False,
    newtonnet_kwargs: dict | None = None,
    opt_kwargs: dict | None = None,
) -> dict:
    """
    # TODO: docstring
    """
    newtonnet_kwargs = newtonnet_kwargs or {}
    opt_kwargs = opt_kwargs or {}

    # Define calculator
    mlcalculator = NewtonNet(
        model_path=SETTINGS.NEWTONNET_MODEL_PATH,
        config_path=SETTINGS.NEWTONNET_CONFIG_PATH,
        **newtonnet_kwargs,
    )
    atoms.calc = mlcalculator

    if use_custom_hessian:
        if optimizer.lower() != "sella":
            raise ValueError("Custom hessian can only be used with Sella.")

        opt_kwargs["diag_every_n"] = 0

        atoms.calc.calculate()
        hessian = atoms.calc.results["hessian"].reshape((-1, 3 * len(atoms)))
        opt_kwargs["hessian_function"] = hessian
    # Run the TS optimization
    dyn = run_ase_opt(
        atoms,
        fmax=fmax,
        max_steps=max_steps,
        optimizer=optimizer,
        opt_kwargs=opt_kwargs,
    )

    return summarize_opt_run(dyn, additional_fields={"name": "NewtonNet TS"})


# TODO: please add the other direction as a literal typehint. Is it backward or reverse?
@ct.electron
def irc_job(
    atoms: Atoms,
    direction: str = Literal["forward"],
    fmax: float = 0.01,
    max_steps: int = 1000,
    newtonnet_kwargs: dict | None = None,
    opt_kwargs: dict | None = None,
) -> dict:
    """
    TODO: docstrings
    """

    newtonnet_kwargs = newtonnet_kwargs or {}
    opt_kwargs = opt_kwargs or {}

    # Define calculator
    mlcalculator = NewtonNet(
        model_path=SETTINGS.NEWTONNET_MODEL_PATH,
        config_path=SETTINGS.NEWTONNET_CONFIG_PATH,
        **newtonnet_kwargs,
    )
    atoms.calc = mlcalculator

    # Run IRC
    run_kwargs = {"direction": direction.lower()}
    dyn = run_ase_opt(
        atoms,
        fmax=fmax,
        max_steps=max_steps,
        optimizer="sella_irc",
        opt_kwargs=opt_kwargs,
        run_kwargs=run_kwargs,
    )

    return summarize_opt_run(dyn, additional_fields={"name": "NewtonNet IRC"})


# TODO: I think it is possible to get rid of all the unit conversion functions
# and instead use the `VibrationsData` class in `ase.vibrations.data.py`
# See details here: https://gitlab.com/ase/ase/-/blob/master/ase/vibrations/data.py
# Once that class is contructed, you can do `VibrationsData.get_frequencies()`
# to return the frequencies in cm^-1, as desired. You can then get rid of
# the `_get_freq_in_cm_inv` and `_mass_weighted_hessian` functions.
@ct.electron
def freq_job(
    atoms: Atoms,
    temperature: float = 298.15,
    pressure: float = 1.0,
    newtonnet_kwargs: dict = None,
) -> dict:
    """
    # TODO: Add docstrings
    """
    newtonnet_kwargs = newtonnet_kwargs or {}

    # Define calculator
    mlcalculator = NewtonNet(
        model_path=SETTINGS.NEWTONNET_MODEL_PATH,
        config_path=SETTINGS.NEWTONNET_CONFIG_PATH,
        **newtonnet_kwargs,
    )
    atoms.calc = mlcalculator

    # Run calculator
    mlcalculator.calculate(atoms)
    hessian = mlcalculator.results["hessian"]

    # Calculate frequencies
    n_atoms = len(atoms)
    hessian_reshaped = np.reshape(hessian, (n_atoms * 3, n_atoms * 3))
    freqs_cm_inv, _ = _get_freq_in_cm_inv(atoms.get_masses(), hessian_reshaped)

    # Sort the frequencies (can remove after ASE MR 2906 is merged)
    freqs_cm_inv = list(freqs_cm_inv)
    freqs_cm_inv.sort(key=np.imag, reverse=True)
    freqs_cm_inv.sort(key=np.real)

    # Make IdealGasThermo object
    igt = ideal_gas(atoms, freqs_cm_inv, energy=mlcalculator.results["energy"])

    # TODO: If you are successful in using the `VibrationsData` class, you
    # can then return the following instead for a much richer and consistent output:
    # return {
    #     "vib": summarize_vib_run(
    #         vibrations_data, additional_fields={"name": "Sella Vibrations"}
    #     ),
    #     "thermo": summarize_thermo_run(
    #         igt,
    #         temperature=temperature,
    #         pressure=pressure,
    #         additional_fields={"name": "Sella Thermo"},
    #     ),
    # }

    return summarize_thermo_run(
        igt,
        temperature=temperature,
        pressure=pressure,
        additional_fields={"name": "NewtonNet Thermo"},
    )


@dataclass
class TSJob:
    """
    TODO: docstring
    """

    ts_electron: Electron = ts_job
    freq_electron: Electron = freq_job
    ts_kwargs: dict | None = None
    freq_kwargs: dict | None = None

    @ct.electron
    def run(self, atoms: Atoms) -> dict:
        """
        TODO: docstring
        """
        ts_kwargs = self.ts_kwargs or {}
        freq_kwargs = self.freq_kwargs or {}

        ts_summary = self.ts_electron(atoms, **ts_kwargs)
        freq_summary = self.freq_electron(ts_summary["atoms"], **freq_kwargs)

        return {"ts": ts_summary, "freq": freq_summary}


@dataclass
class IRCJob:
    """
    TODO: docstring
    """

    irc_electron: Electron = irc_job
    freq_electron: Electron = freq_job
    irc_kwargs: dict | None = None
    freq_kwargs: dict | None = None

    @ct.electron
    def run(self, atoms: Atoms) -> dict:
        """
        TODO: docstring
        """

        irc_kwargs = self.irc_kwargs or {}
        freq_kwargs = self.freq_kwargs or {}

        irc_summary = self.irc_electron(atoms, **irc_kwargs)
        freq_summary = self.freq_electron(irc_summary["atoms"], **freq_kwargs)

        return {"irc": irc_summary, "freq": freq_summary}


@dataclass
class QuasIRCJob:
    """
    TODO: docstring
    """

    irc_electron: Electron = irc_job
    relax_electron: Electron = relax_job
    freq_electron: Electron = freq_job
    irc_kwargs: dict | None = None
    relax_kwargs: dict | None = None
    freq_kwargs: dict | None = None

    @ct.electron
    def run(self, atoms: Atoms) -> dict:
        """
        TODO: docstring
        """

        irc_kwargs = self.irc_kwargs or {}
        irc_kwargs = irc_kwargs | {"max_steps": 5}

        relax_kwargs = self.relax_kwargs or {}

        freq_kwargs = self.freq_kwargs or {}

        irc_summary = self.irc_electron(atoms, **irc_kwargs)
        relax_summary = self.relax_electron(irc_summary["atoms"], **relax_kwargs)
        freq_summary = self.freq_electron(relax_summary["atoms"], **freq_kwargs)

        return {"irc": irc_summary, "relax": relax_summary, "freq": freq_summary}


# TODO: Can potentially replace with `VibrationsData` (see above)
def _get_freq_in_cm_inv(
    masses: np.array, reshaped_hessian: np.ndarray
) -> list[np.array, np.array]:
    # Calculate mass-weighted Hessian
    mass_weighted_hessian = _mass_weighted_hessian(masses, reshaped_hessian)

    # Calculate eigenvalues and eigenvectors
    eigvals, eigvecs = np.linalg.eig(mass_weighted_hessian)
    eigvals = np.sort(np.real(eigvals))

    # Calculate frequencies in cm^-1
    freqs = np.emath.sqrt(eigvals) * fs * (10**15) / (_c * 100 * 2 * np.pi)
    return freqs, eigvecs


# TODO: Can potentially replace with `VibrationsData` (see above)
def _mass_weighted_hessian(masses: np.array, hessian: np.ndarray) -> np.ndarray:
    """
    Calculates the mass-weighted Hessian matrix.

    Parameters:
        masses (array): An array of atom masses.
        hessian (ndarray): A 2D numpy array representing the Hessian matrix.

    Returns:
        mass_weighted_hessian (ndarray): A 2D numpy array representing the mass-weighted Hessian matrix.

    Raises:
        ValueError: If the dimensions of masses and hessian are not compatible.

    The mass-weighted Hessian matrix is calculated by dividing each element of the Hessian matrix
    by the square root of the product of the masses of the corresponding atoms. The resulting matrix
    represents the second derivatives of the potential energy surface, taking into account the masses
    of the atoms.

    The input hessian is assumed to be a square matrix of size 3N x 3N, where N is the number of atoms.
    The input masses should have N elements, where each element corresponds to the mass of an atom.

    The returned mass_weighted_hessian matrix will have the same dimensions as the input hessian.

    Example:
        masses = [12.01, 1.008, 1.008, 16.00, 1.008, 1.008, 1.008]
        hessian = np.zeros((21, 21))  # Example Hessian matrix
        mass_weighted_hessian = _mass_weighted_hessian(masses, hessian)
    """

    if len(masses) != hessian.shape[0] // 3 or hessian.shape[0] != hessian.shape[1]:
        raise ValueError("Incompatible dimensions of masses and hessian.")

    sqrt_masses = np.sqrt(np.outer(masses, masses))
    return hessian / np.tile(sqrt_masses, (3, 3))
