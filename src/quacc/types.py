"""
Custom types used throughout quacc.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic_settings import BaseSettings


class DefaultSetting(BaseSettings):
    """
    Type hint for when a default setting will be applied
    """


if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from pathlib import Path
    from typing import Any, Literal

    from ase.atoms import Atoms
    from ase.md.md import MolecularDynamics
    from ase.optimize.optimize import Dynamics
    from emmet.core.math import ListMatrix3D, Matrix3D, Vector3D
    from emmet.core.symmetry import CrystalSystem
    from emmet.core.vasp.calc_types import CalcType
    from emmet.core.vasp.calc_types.enums import RunType, TaskType
    from emmet.core.vasp.calculation import VaspObject
    from emmet.core.vasp.task_valid import TaskState
    from numpy.random import Generator
    from numpy.typing import ArrayLike, NDArray
    from pymatgen.core.composition import Composition
    from pymatgen.core.lattice import Lattice
    from pymatgen.core.periodic_table import Element
    from pymatgen.core.structure import Molecule, Structure
    from pymatgen.entries.computed_entries import ComputedEntry
    from pymatgen.io.vasp.inputs import Incar, Kpoints, Poscar, Potcar
    from typing_extensions import NotRequired, TypedDict

    # ----------- File handling -----------

    Filenames = str | Path | list[str | Path]
    SourceDirectory = str | Path

    # ----------- k-point handling -----------

    class PmgKpts(TypedDict, total=False):
        """
        Type hint for `pmg_kpts` in [quacc.utils.kpts.convert_pmg_kpts][].
        """

        line_density: float
        kppvol: float
        kppa: float
        length_densities: tuple[float, float, float]

    # ----------- Runner parameter type hints -----------

    class OptParams(TypedDict, total=False):
        """
        Type hint for `opt_params` used throughout quacc.
        """

        relax_cell: bool
        fmax: float | None
        max_steps: int
        optimizer: Dynamics
        optimizer_kwargs: dict[str, Any] | None
        store_intermediate_results: bool
        fn_hook: Callable | None
        run_kwargs: dict[str, Any] | None

    class MDParams(TypedDict, total=False):
        """
        Type hint for `md_params` used throughout quacc.
        """

        dynamics: MolecularDynamics
        dynamics_kwargs: dict[str, Any] | None
        steps: int
        maxwell_boltzmann_kwargs: MaxwellBoltzmanDistributionKwargs | None
        set_com_stationary: bool
        set_zero_rotation: bool

    class VibKwargs(TypedDict, total=False):
        """
        Type hint for `vib_kwargs` in [quacc.runners.ase.Runner.run_vib][].
        """

        indices: list[int] | None
        delta: float
        nfree: int

    class MaxwellBoltzmanDistributionKwargs(TypedDict, total=False):
        """
        Type hint for `maxwell_boltzmann_kwargs` in [quacc.runners.ase.Runner.run_md][].
        """

        temperature_K: float
        force_temp: bool
        rng: Generator | None

    # ----------- Atoms handling type hints -----------

    class AdsSiteFinderKwargs(TypedDict, total=False):
        """
        Type hint for `ads_site_finder_kwargs` in [quacc.atoms.slabs.make_adsorbate_structures][].
        """

        selective_dynamics: bool  # default = False
        height: float  # default = 0.9
        mi_vec: ArrayLike | None  # default = None

    class FindAdsSitesKwargs(TypedDict, total=False):
        """
        Type hint for `find_ads_sites_kwargs` in [quacc.atoms.slabs.make_adsorbate_structures][].
        """

        distance: float  # default = 2.0
        put_inside: bool  # default = True
        symm_reduce: float  # default = 1e-2
        near_reduce: float  # default = 1e-2
        positions: list[
            Literal["ontop", "bridge", "hollow", "subsurface"]
        ]  # default: ["ontop", "bridge", "hollow"]
        no_obtuse_hollow: bool  # default = True

    # ----------- Custom calculator type hints -----------

    class QchemResults(TypedDict, total=False):
        """
        Type hint for the `results` attribute in [quacc.calculators.qchem.qchem.QChem][].
        """

        energy: float  # electronic energy in eV
        taskdoc: dict[str, Any]  # Output from `emmet.core.qc_tasks.TaskDoc`
        hessian: NotRequired[NDArray]  # Hessian in eV/A^2/amu
        forces: NotRequired[NDArray]  # forces in eV/A

    class VaspJobKwargs(TypedDict, total=False):
        """
        Type hint for `vasp_job_kwargs` in in [quacc.calculators.vasp.vasp_custodian.run_custodian][].
        """

        output_file: str  # default = "vasp.out"
        stderr_file: str  # default = "std_err.txt"
        suffix: str  # default = ""
        final: bool  # default = True
        backup: bool  # default = True
        auto_npar: bool  # default = False
        auto_gamma: bool  # default = True
        settings_override: dict | None  # default = None
        copy_magmom: bool  # default = False
        auto_continue: bool  # default = False

    class VaspCustodianKwargs(TypedDict, total=False):
        """
        Type hint for `custodian_kwargs` in [quacc.calculators.vasp.vasp_custodian.run_custodian][].
        """

        max_errors_per_job: int | None  # default = None
        polling_time_step: int  # default = 10
        monitor_freq: int  # default = 10
        skip_over_errors: bool  # default = False
        gzipped_output: bool  # default = False
        checkpoint: bool  # default = False
        terminate_func: Callable | None  # default = None
        terminate_on_nonzero_returncode: bool  # default = False

    # ----------- ASE calculator type hints -----------

    class Results(TypedDict):
        """Dictionary of results from atoms.calc.results"""

    class Parameters(TypedDict):
        """Dictionary of parameters from atoms.calc.parameters"""

    # ----------- ASE dynamics type hints -----------

    class ParametersDyn(TypedDict):
        """Dictionary of parameters from Dynamics.todict()"""

    class TrajectoryLog(TypedDict):
        """Dictionary of parameters related to the MD trajectory"""

        # ASE units
        kinetic_energy: float
        temperature: float
        time: float

    # ----------- Emmet type hints -----------

    class SymmetryData(TypedDict):
        """Type hint associated with [emmet.core.symmetry.SymmetryData][]"""

        crystal_system: CrystalSystem
        symbol: str
        number: int
        point_group: str
        symprec: float
        version: str

    class PointGroupData(TypedDict):
        """Type hint associated with [emmet.core.symmetry.PointGroupData][]"""

        point_group: str
        rotation_number: float
        linear: bool
        tolerance: float
        eigen_tolerance: float
        matrix_tolerance: float

    class EmmetBase(TypedDict):
        """Type hint associated with `emmet.core.base.EmmetBaseModel`."""

        emmet_version: str
        pymatgen_version: str
        pull_request: int | None
        database_version: str | None
        build_date: datetime
        license: Literal["BY-C", "BY-NC"]

    class StructureMetadata(EmmetBase):
        """Type hint associated with [emmet.core.structure.StructureMetadata][]"""

        nsites: int
        elements: list[Element]
        nelements: int
        composition: Composition
        formula_pretty: str
        formula_anonymous: str
        chemsys: str
        volume: float
        density: float
        density_atomic: float
        symmetry: SymmetryData

    class MoleculeMetadata(EmmetBase):
        """Type hint associated with [emmet.core.structure.MoleculeMetadata][]"""

        charge: int
        spin_multiplicity: int
        natoms: int
        elements: list[Element]
        nelements: int
        nelectrons: int
        composition: Composition
        composition_reduced: Composition
        formula_alphabetical: str
        formula_pretty: str
        formula_anonymous: str
        chemsys: str
        symmetry: PointGroupData

    class PotcarSpec(TypedDict):
        """Type hint associated with emmet.core.vasp.calculation.PotcarSpec."""

        titel: str
        hash: str

    class CalculationInput(TypedDict):
        """Type hint associated with emmet.core.vasp.calculation.CalculationInput."""

        incar: dict[str, Any]
        kpoints: dict[str, Any]
        nkpoints: int
        potcar: list[str]
        potcar_spec: list[PotcarSpec]
        potcar_type: list[str]
        parameters: dict[str, Any]
        lattice_rec: Lattice
        structure: Structure
        is_hubbard: bool
        hubbards: dict[str, float]

    class ElectronicStep(TypedDict):
        """Type hint associated with emmet.core.vasp.calculation.ElectronicStep."""

        alphaZ: float
        ewald: float
        hartreedc: float
        XCdc: float
        pawpsdc: float
        pawaedc: float
        eentropy: float
        bandstr: float
        atom: float
        e_fr_energy: float
        e_wo_entrp: float
        e_0_energy: float

    class IonicStep(TypedDict):
        """Type hint associated with emmet.core.vasp.calculation.IonicStep."""

        e_fr_energy: float
        e_wo_entrp: float
        e_0_energy: float
        forces: list[Vector3D]
        stress: Matrix3D
        electronic_steps: list[ElectronicStep]
        structure: Structure

    class FrequencyDependentDielectric(TypedDict):
        """Type hint associated with
        emmet.core.vasp.calculation.FrequencyDependentDielectric.
        """

        real: list[list[float]]
        imaginary: list[list[float]]
        energy: list[float]

    class ElectronPhononDisplacedStructures(TypedDict):
        """Type hint associated with
        emmet.core.vasp.calculation.ElectronPhononDisplacedStructures.
        """

        temperatures: list[float]
        structures: list[Structure]

    class RunStatistics(TypedDict):
        """Type hint associated with emmet.core.vasp.calculation.RunStatistics."""

        average_memory: float
        max_memory: float
        elapsed_time: float
        system_time: float
        user_time: float
        total_time: float
        cores: int

    class CalculationOutput(TypedDict, total=False):
        """Type hint associated with emmet.core.vasp.calculation.CalculationOutput."""

        energy: float
        energy_per_atom: float
        structure: Structure
        efermi: float
        is_metal: bool
        bandgap: float
        cbm: float
        vbm: float
        is_gap_direct: bool
        direct_gap: float
        transition: str
        mag_density: float
        epsilon_static: ListMatrix3D
        epsilon_static_wolfe: ListMatrix3D
        epsilon_ionic: ListMatrix3D
        frequency_dependent_dielectric: FrequencyDependentDielectric
        ionic_steps: list[IonicStep]
        locpot: dict[int, list[float]]
        outcar: dict[str, Any]
        force_constants: list[list[Matrix3D]]
        normalmode_frequencies: list[float]
        normalmode_eigenvals: list[float]
        normalmode_eigenvecs: list[list[Vector3D]]
        elph_displaced_structures: ElectronPhononDisplacedStructures
        dos_properties: dict[str, dict[str, dict[str, float]]]
        run_stats: RunStatistics

    class Calculation(TypedDict):
        """Type hint associated with emmet.core.vasp.calculation.Calculation."""

        dir_name: str
        vasp_version: str
        has_vasp_completed: TaskState | bool
        input: CalculationInput
        output: CalculationOutput
        completed_at: str
        task_name: str
        output_file_paths: dict[str, str]
        bader: dict
        run_type: RunType
        task_type: TaskType
        calc_type: CalcType

    class OrigInputs(TypedDict):
        """Type hint associated with emmet.core.tasks.OrigInputs."""

        incar: Incar
        poscar: Poscar
        kpoints: Kpoints
        potcar: Potcar

    class OutputDoc(TypedDict):
        """Type hint associated with emmet.core.tasks.OutputDoc."""

        structure: Structure
        density: float
        energy: float
        forces: list[list[float]]
        stress: list[list[float]]
        energy_per_atom: float
        bandgap: float

    class CustodianDoc(TypedDict):
        """Type hint associated with emmet.core.tasks.CustodianDoc."""

        corrections: list[Any]
        job: dict

    class AnalysisDoc(TypedDict):
        """Type hint associated with emmet.core.tasks.AnalysisDoc."""

        delta_volume: float
        delta_volume_percent: float
        max_force: float
        warnings: list[str]
        errors: list[str]

    class TaskDoc(StructureMetadata):
        """Type hint associated with emmet.core.tasks.TaskDoc."""

        tags: list[str] | None
        dir_name: str
        state: TaskState
        calcs_reversed: list[Calculation]
        structure: Structure
        task_type: CalcType | TaskType
        task_id: str
        orig_inputs: OrigInputs
        output: OutputDoc
        included_objects: VaspObject
        vasp_objects: dict[VaspObject, Any]
        entry: ComputedEntry
        task_label: str
        author: str
        transformations: dict[str, Any]
        additional_json: dict[str, Any]
        custodian: list[CustodianDoc]
        analysis: AnalysisDoc
        last_updated: datetime

    # ----------- Schema (Atoms) type hints -----------

    class AtomsSchema(StructureMetadata, MoleculeMetadata):
        """Type hint associated with [quacc.schemas.atoms.atoms_to_metadata][]"""

        atoms: Atoms
        structure: Structure  # if atoms.pbc.any()
        molecule: Molecule  # if not atoms.pbc.any()

    # ----------- Schema (ASE) type hints -----------

    class RunSchema(AtomsSchema):
        """Schema for [quacc.schemas.ase.Summarize.run][]"""

        input_atoms: AtomsSchema | None
        nid: str
        dir_name: str
        parameters: Parameters
        results: Results
        quacc_version: str

    class OptSchema(RunSchema):
        """Schema for [quacc.schemas.ase.Summarize.opt][]"""

        parameters_opt: ParametersDyn
        converged: bool
        trajectory: list[Atoms]
        trajectory_results: list[Results]

    class DynSchema(RunSchema):
        """Schema for [quacc.schemas.ase.Summarize.md][]"""

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

    class ParametersThermo(TypedDict):
        # ASE units
        temperature: float
        pressure: float
        sigma: int
        spin_multiplicity: int
        vib_freqs: list[float]
        vib_energies: list[float]
        n_imag: int

    class ThermoResults(TypedDict):
        # ASE units
        energy: float
        enthalpy: float
        entropy: float
        gibbs_energy: float
        zpe: float

    class ThermoSchema(AtomsSchema):
        parameters_thermo: ParametersThermo
        results: ThermoResults

    class VibThermoSchema(VibSchema, ThermoSchema):
        """Combined Vibrations and Thermo schema"""

    # ----------- Schema (phonons) type hints -----------

    class ThermalProperties(TypedDict):
        """Type hint associated with PhononSchema."""

        temperatures: NDArray
        free_energy: NDArray
        entropy: NDArray
        heat_capacity: NDArray

    class MeshProperties(TypedDict):
        """Type hint associated with PhononSchema."""

        qpoints: NDArray
        weights: NDArray
        frequencies: NDArray
        eigenvectors: NDArray
        group_velocities: NDArray

    class DosProperties(TypedDict):
        """Type hint associated with PhononSchema."""

        frequency_points: NDArray
        total_dos: NDArray

    class PhononResults(TypedDict):
        thermal_properties: ThermalProperties
        mesh_properties: MeshProperties
        total_dos: DosProperties
        force_constants: NDArray

    class PhonopyMetadata(TypedDict):
        """Type hint associated with PhononSchema."""

        version: str

    class PhononSchema(AtomsSchema):
        """Type hint associated with [quacc.schemas.phonons.summarize_phonopy][]"""

        parameters: dict[str, Any] | None
        nid: str
        dir_name: str
        phonopy_metadata: PhonopyMetadata
        results: PhononResults
        quacc_version: str

    # ----------- Schema (VASP) type hints -----------

    class BaderSchema(TypedDict, total=False):
        """Type hint associated with quacc.schemas.vasp._bader_runner."""

        atomic_volume: float
        partial_charges: list[float]
        spin_moments: list[float]
        bader_version: float
        min_dist: list[float]

    class DDECSchema(TypedDict, total=False):
        """Type hint associated with quacc.schemas.vasp._ddec_runner."""

        partial_charges: list[float]
        spin_moments: list[float]
        dipoles: list[float]
        bond_order_sums: list[float]
        bond_order_dict: dict
        rsquared_moments: list[float]
        rcubed_moments: list[float]
        rfourth_moments: list[float]

    class CM5Schema(TypedDict):
        """Type hint used in DDECSchema"""

        partial_charges: list[float]

    class ChargemolSchema(TypedDict, total=False):
        """Type hint associated with quacc.schemas.vasp._chargemol_runner`"""

        ddec: DDECSchema
        cm5: CM5Schema

    class VaspSchema(RunSchema, TaskDoc):
        """Type hint associated with [quacc.schemas.vasp.VaspSummarize.run][]"""

        bader: BaderSchema
        chargemol: ChargemolSchema
        steps: dict[int, TaskDoc]  # when store_intermediate_results=True

    # ----------- Recipe (VASP) type hints -----------

    class DoubleRelaxSchema(TypedDict):
        """Type hint associated with the double relaxation jobs."""

        relax1: VaspSchema
        relax2: VaspSchema

    class MPRelaxFlowSchema(VaspSchema):
        """Type hint associated with the MP relaxation flows."""

        pre_relax: VaspSchema
        relax: VaspSchema
        static: VaspSchema

    class QMOFRelaxSchema(VaspSchema):
        """Type hint associated with the QMOF relaxation jobs."""

        prerelax_lowacc: VaspSchema | None
        position_relax_lowacc: VaspSchema
        volume_relax_lowacc: VaspSchema | None
        double_relax: VaspSchema

    class VaspASEOptSchema(VaspSchema, OptSchema):
        """Type hint associated with VASP relaxations run via ASE"""

    # ----------- Recipe (Espresso) type hints -----------
    class SystemData(TypedDict):
        occupations: str
        smearing: str
        degauss: float

    class ElectronsData(TypedDict):
        conv_thr: float
        mixing_mode: str
        mixing_beta: float

    class InputData(TypedDict):
        system: SystemData
        electrons: ElectronsData
        control: NotRequired[dict[str, Any]]

    class EspressoBaseSet(TypedDict):
        input_data: InputData
        kspacing: float

    class EspressoBandsSchema(TypedDict, total=False):
        bands_pw: RunSchema
        bands_pp: RunSchema
        fermi_surface: RunSchema

    class EspressoDosSchema(TypedDict):
        static_job: RunSchema
        non_scf_job: RunSchema
        dos_job: RunSchema

    class EspressoProjwfcSchema(TypedDict):
        static_job: RunSchema
        non_scf_job: RunSchema

    class EspressoPhononDosSchema(TypedDict):
        phonon_job: RunSchema
        q2r_job: RunSchema
        matdyn_job: RunSchema

    # ----------- Recipe (NewtonNet) type hints -----------

    class NewtonNetTSSchema(OptSchema):
        freq_job: VibThermoSchema | None

    class NewtonNetIRCSchema(OptSchema):
        freq_job: VibThermoSchema | None

    class NewtonNetQuasiIRCSchema(OptSchema):
        irc_job: NewtonNetIRCSchema
        freq_job: VibThermoSchema | None

    # ----------- Recipe (Q-Chem) type hints -----------

    class QchemQuasiIRCSchema(OptSchema):
        initial_irc: OptSchema
