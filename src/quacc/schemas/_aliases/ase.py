"""Aliases for type hinting `quacc.schemas.ase`"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from quacc.schemas._aliases.atoms import AtomsSchema

if TYPE_CHECKING:
    from ase.atoms import Atoms
    from numpy.typing import NDArray


class Results(TypedDict):
    """Dictionary of results from atoms.calc.results"""


class Parameters(TypedDict):
    """Dictionary of parameters from atoms.calc.parameters"""


class ParametersDyn(TypedDict):
    """Dictionary of parameters from Dynamics.todict()"""


class TrajectoryLog(TypedDict):
    """Dictionary of parameters related to the MD trajectory"""

    kinetic_energy: float
    temperature: float
    time: float


class RunSchema(AtomsSchema):
    """Schema for [quacc.schemas.ase.summarize_run][]"""

    input_atoms: AtomsSchema | None
    nid: str
    dir_name: str
    parameters: Parameters
    results: Results
    quacc_version: str


class OptSchema(RunSchema):
    """Schema for [quacc.schemas.ase.summarize_opt_run][]"""

    parameters_opt: ParametersDyn
    converged: bool
    trajectory: list[Atoms]
    trajectory_results: list[Results]


class DynSchema(RunSchema):
    """Schema for [quacc.schemas.ase.summarize_md_run][]"""

    parameters_md: ParametersDyn
    trajectory: list[Atoms]
    trajectory_log: TrajectoryLog
    trajectory_results: list[Results]


class ParametersVib(TypedDict):
    delta: float
    direction: str
    method: str
    ndof: int
    nfree: int


class VibResults(TypedDict):
    imag_vib_freqs: int
    n_imag: int
    vib_energies: list[float]
    vib_freqs: list[float]
    vib_energies_raw: list[float]
    vib_freqs_raw: list[float]


class VibSchema(AtomsSchema):
    parameters: Parameters | None
    parameters_vib: ParametersVib | None
    results: VibResults


class PhononSchema(RunSchema):
    """Schema for [quacc.schemas.phonons.summarize_phonopy][]"""

    force_constant: NDArray


class ParametersThermo(TypedDict):
    temperature: float
    pressure: float
    sigma: int
    spin_multiplicity: int
    vib_freqs: list[float]
    vib_energies: list[float]
    n_imag: int


class ThermoResults(TypedDict):
    energy: float
    enthalpy: float
    entropy: float
    gibbs_energy: float
    zpe: float


class ThermoSchema(AtomsSchema):
    parameters_thermo: ParametersThermo
    results: ThermoResults


class VibThermoSchema(VibSchema, ThermoSchema):
    """Schema for [quacc.schemas.ase.summarize_vib_and_thermo][]"""
