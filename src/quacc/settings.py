"""Settings for quacc."""

from __future__ import annotations

import inspect
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from random import randint
from shutil import which
from typing import TYPE_CHECKING, Literal, Optional, Union

import psutil
from maggma.core import Store
from monty.serialization import loadfn
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from typing import Any, Callable

_DEFAULT_CONFIG_FILE_PATH = Path("~", ".quacc.yaml").expanduser().resolve()


class QuaccSettings(BaseSettings):
    """
    Settings for quacc.

    The default way to modify these is to make a ~/.quacc.yaml file. Alternatively, the
    environment variable QUACC_CONFIG_FILE can be set to point to a custom yaml file
    with quacc settings. The quacc CLI offers a `quacc set <setting> <value>` option to
    do this as well.

    The variables can also be modified individually though environment variables by
    using the "QUACC" prefix. e.g. `export QUACC_SCRATCH_DIR=/path/to/scratch`.
    """

    model_config = SettingsConfigDict(
        env_prefix="quacc_",
        env_nested_delimiter="__",
        env_parse_none_str="None",
        extra="forbid",
        validate_assignment=True,
    )

    CONFIG_FILE: Path = Field(
        _DEFAULT_CONFIG_FILE_PATH,
        description=(
            """
            Path to the YAML file to load alternative quacc configuration
            defaults from.
            """
        ),
    )

    # --8<-- [start:settings]

    # ---------------------------
    # Workflow Engine
    # ---------------------------

    WORKFLOW_ENGINE: Optional[
        Literal["covalent", "dask", "parsl", "prefect", "redun", "jobflow"]
    ] = Field(None, description=("The workflow manager to use, if any."))

    # ---------------------------
    # General Settings
    # ---------------------------

    RESULTS_DIR: Path = Field(
        Path.cwd(),
        description=(
            """
            Directory to permanently store I/O-based calculation results in.
            Note that this behavior may be modified by the chosen workflow engine.
            """
        ),
    )
    SCRATCH_DIR: Optional[Path] = Field(
        None,
        description=(
            """
            The base directory where calculations are run. If set to None, calculations will be run in a
            temporary directory within `RESULTS_DIR`. If a `Path` is supplied, calculations will
            be run in a temporary directory within `SCRATCH_DIR`. Files are always moved back
            to `RESULTS_DIR` after the calculation is complete, and the temporary directory
            in `SCRATCH_DIR` is removed.
            """
        ),
    )
    CREATE_UNIQUE_DIR: bool = Field(
        True,
        description=(
            """
            Whether to have a unique directory in RESULTS_DIR for each job.
            Some workflow engines have an option to do this for you already,
            in which case you should set this to False.
            """
        ),
    )
    NESTED_RESULTS_DIR: bool = Field(
        True,
        description=(
            """
            Whether to automatically nest the results directories by the calling flow, subflow, etc.
            """
        ),
    )
    GZIP_FILES: bool = Field(
        True, description="Whether generated files should be gzip'd."
    )
    CHECK_CONVERGENCE: bool = Field(
        True,
        description="Whether to check for convergence, when implemented by a given recipe.",
    )

    # ---------------------------
    # Data Store Settings
    # ---------------------------
    STORE: Optional[Union[dict[str, dict], Store]] = Field(
        None,
        description=(
            """
            The desired Maggma data store where calculation results will be stored. All data stores listed in
            `maggma.stores.__init__.py` are supported. If a dictionary is provided, the first key must be set
            to the desired store type. The sub-parameters are the keyword arguments accepted by the Store.
            An example is shown below:

            ```yaml
            STORE:
              MongoStore:
                database: my_db
                collection_name: my_collection
                username: my_username
                password: my_password
                host: localhost
                port: 27017
            ```
            """
        ),
    )

    # ---------------------------
    # Prefect Settings
    # ---------------------------
    PREFECT_AUTO_SUBMIT: bool = Field(
        True, description="Whether to auto-submit tasks to the task runner."
    )

    # ---------------------------
    # ORCA Settings
    # ---------------------------
    ORCA_CMD: str = Field(
        which("orca") or "orca",
        description=(
            """
            Path to the ORCA executable. This must be the full, absolute path
            for parallel calculations to work.
            """
        ),
    )

    # ---------------------------
    # ESPRESSO Settings
    # ---------------------------
    ESPRESSO_BIN_DIR: Path = Field(
        Path(), description="Base path to the espresso binaries."
    )
    ESPRESSO_BINARIES: dict[str, str] = Field(
        {
            "pw": "pw.x",
            "ph": "ph.x",
            "neb": "neb.x",
            "q2r": "q2r.x",
            "dos": "dos.x",
            "matdyn": "matdyn.x",
            "dynmat": "dynmat.x",
            "bands": "bands.x",
            "projwfc": "projwfc.x",
            "pp": "pp.x",
            "wannier90": "wannier90.x",
            "fs": "fs.x",
            "postahc": "postahc.x",
            "dvscf_q2r": "dvscf_q2r.x",
        },
        description="Name for each espresso binary.",
    )
    ESPRESSO_PARALLEL_CMD: Union[str, tuple[str, str]] = Field(
        "",
        description=(
            """
            Parallelization flags to run Espresso. The 0th index of the tuple
            contains any commands that come before the binary, and the 1st index
            contains any commands that come after the binary.

            For example: ["mpirun -np 4", "-nk 2"] would be the same as running
            Espresso via `"mpirun -np 4 {binary} -nk 2"` where {binary} is the
            binary that is automatically determined based on the job type,
            `ESPRESSO_BIN_DIR` and `ESPRESSO_BINARIES`.

            If only a `str` is provided, no post-binary commands will be used.
            """
        ),
    )
    ESPRESSO_PSEUDO: Optional[Path] = Field(
        None, description=("Path to a pseudopotential library for espresso.")
    )
    ESPRESSO_PRESET_DIR: Path = Field(
        Path(__file__).parent / "calculators" / "espresso" / "presets",
        description="Path to the espresso preset directory",
    )

    # ---------------------------
    # Gaussian Settings
    # ---------------------------
    GAUSSIAN_CMD: str = Field("g16", description=("Path to the Gaussian executable."))

    # ---------------------------
    # ONETEP Settings
    # ---------------------------
    ONETEP_CMD: str = Field(
        "onetep.arch",
        description=("Full ONETEP command, including parallelization flags."),
    )
    ONETEP_PP_PATH: Path = Field(Path(), description=("Path to pseudopotentials."))

    # ---------------------------
    # GULP Settings
    # ---------------------------
    GULP_CMD: str = Field("gulp", description=("Path to the GULP executable."))
    GULP_LIB: Optional[Path] = Field(
        None,
        description=(
            "Path to the GULP force field library. If not specified, the GULP_LIB environment variable will be used (if present)."
        ),
    )

    # ---------------------------
    # VASP Settings
    # ---------------------------

    # VASP Settings: Main
    VASP_PARALLEL_CMD: str = Field(
        "",
        description=(
            """
            Parallel command to run VASP with Custodian.
            For example: `"srun -N 2 --ntasks-per-node 48"`.
            Note that this does not include the executable name.
            """
        ),
    )
    VASP_CMD: str = Field(
        "vasp_std", description="Command to run the standard version of VASP."
    )
    VASP_GAMMA_CMD: str = Field(
        "vasp_gam", description="Command to run the gamma-point only version of VASP."
    )
    VASP_PP_PATH: Optional[Path] = Field(
        None,
        description="Path to the VASP pseudopotential library. Must contain the directories `potpaw_PBE` and `potpaw` for PBE and LDA pseudopotentials, respectively.",
    )
    VASP_VDW: Optional[Path] = Field(
        None, description="Path to the vdw_kernel.bindat file for VASP vdW functionals."
    )

    # VASP Settings: General
    VASP_INCAR_COPILOT: Literal["off", "on", "aggressive"] = Field(
        "on",
        description=(
            """
            Controls VASP co-pilot mode for automated INCAR parameter handling.
            off: Do not use co-pilot mode. INCAR parameters will be unmodified.
            on: Use co-pilot mode. This will only modify INCAR flags not already set by the user.
            aggressive: Use co-pilot mode in aggressive mode. This will modify INCAR flags even if they are already set by the user.
            """
        ),
    )
    VASP_BADER: bool = Field(
        bool(which("bader")),
        description=(
            """"
            Whether to run a Bader analysis when summarizing VASP results.
            Requires bader to be in PATH.
            """
        ),
    )
    VASP_CHARGEMOL: bool = Field(
        bool(os.environ.get("DDEC6_ATOMIC_DENSITIES_DIR")),
        description=(
            """
            Whether to run a Chargemol (i.e. DDEC6, CM5) analysis when summarizing VASP results.
            Requires the Chargemol executable to be in PATH and the DDEC6_ATOMIC_DENSITIES_DIR environment variable.
            """
        ),
    )
    VASP_PRESET_MAG_DEFAULT: float = Field(
        1.0,
        description=(
            """
            Default initial magmom to use for a given element if a preset
            with magmoms is provided but an element is missing from the list.
            """
        ),
    )
    VASP_MAG_CUTOFF: float = Field(
        0.02,
        description=(
            """
            If the absolute value of all magnetic moments are below this value,
            they will be set to 0 such that a spin-unpolarized calculation will be performed.
            """
        ),
    )
    VASP_COPY_MAGMOMS: bool = Field(
        True,
        description=(
            """
            If True, any pre-existing atoms.get_magnetic_moments() will be set
            in atoms.set_initial_magnetic_moments().
            """
        ),
    )
    VASP_PRESET_DIR: Path = Field(
        Path(__file__).parent / "calculators" / "vasp" / "presets",
        description="Path to the VASP preset directory",
    )

    # VASP Settings: Custodian
    VASP_USE_CUSTODIAN: bool = Field(
        True, description="Whether Custodian should be used to run VASP"
    )
    VASP_CUSTODIAN_VTST: bool = Field(
        False,
        description=(
            """
            If VTST-related input swaps should be used when running Custodian.
            Requires VASP to be compiled with VTST
            """
        ),
    )
    VASP_CUSTODIAN_MAX_ERRORS: int = Field(
        5, description="Maximum errors for Custodian"
    )
    VASP_CUSTODIAN_HANDLERS: list[str] = Field(
        [
            "VaspErrorHandler",
            "MeshSymmetryErrorHandler",
            "UnconvergedErrorHandler",
            "NonConvergingErrorHandler",
            "PotimErrorHandler",
            "PositiveEnergyErrorHandler",
            "FrozenJobErrorHandler",
            "StdErrHandler",
            "LargeSigmaHandler",
            "IncorrectSmearingHandler",
        ],
        description="Handlers for Custodian",
    )
    VASP_CUSTODIAN_VALIDATORS: list[str] = Field(
        ["VasprunXMLValidator", "VaspFilesValidator"],
        description="Validators for Custodian",
    )
    VASP_CUSTODIAN_WALL_TIME: Optional[int] = Field(
        None,
        description=(
            """
            After this many seconds, Custodian will stop running
            and ensure that VASP writes a STOPCAR
            """
        ),
    )

    # ---------------------------
    # Q-Chem Settings
    # ---------------------------

    # Q-Chem Settings: Main
    QCHEM_CMD: str = Field(
        "qchem", description="Command to run the standard version of Q-Chem."
    )

    QCHEM_LOCAL_SCRATCH: Path = Field(
        Path("/tmp") if Path("/tmp").exists() else Path.cwd() / ".qchem_scratch",
        description="Compute-node local scratch directory in which Q-Chem should perform IO.",
    )
    QCHEM_NUM_CORES: int = Field(
        psutil.cpu_count(logical=False),
        description="Number of cores to use for the Q-Chem calculation.",
    )

    # Q-Chem Settings: Custodian
    QCHEM_USE_ERROR_HANDLERS: bool = Field(
        True,
        description="Whether Custodian's error handlers should be employed for Q-Chem.",
    )

    QCHEM_CUSTODIAN_MAX_ERRORS: int = Field(
        5, description="Maximum errors for Q-Chem Custodian."
    )

    # NBO Settings
    QCHEM_NBO_EXE: Optional[Path] = Field(
        None, description="Full path to the NBO executable."
    )

    # ---------------------------
    # NewtonNet Settings
    # ---------------------------
    NEWTONNET_MODEL_PATH: Union[Path, list[Path]] = Field(
        "best_model_state.tar", description="Path to NewtonNet .tar model"
    )
    NEWTONNET_CONFIG_PATH: Union[Path, list[Path]] = Field(
        "config.yml", description="Path to NewtonNet YAML settings file"
    )

    # ---------------------------
    # Logger Settings
    # ---------------------------
    LOG_FILENAME: Optional[Path] = Field(
        None, description="Path to store the log file."
    )
    LOG_LEVEL: Optional[Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]] = (
        Field("INFO", description=("Logger level."))
    )

    # --8<-- [end:settings]

    @field_validator(
        "RESULTS_DIR",
        "SCRATCH_DIR",
        "ESPRESSO_PRESET_DIR",
        "ESPRESSO_PSEUDO",
        "GULP_LIB",
        "QCHEM_LOCAL_SCRATCH",
        "NEWTONNET_MODEL_PATH",
        "VASP_PRESET_DIR",
        "VASP_PP_PATH",
        "VASP_VDW",
    )
    @classmethod
    def expand_paths(cls, v: Optional[Path]) -> Optional[Path]:
        """Expand ~/ and $ENV_VARS in paths."""
        if v:
            v = Path(os.path.expandvars(v)).expanduser()
        return v

    @field_validator("RESULTS_DIR", "SCRATCH_DIR")
    @classmethod
    def make_directories(cls, v: Optional[Path]) -> Optional[Path]:
        """Make directories."""
        if v:
            v.mkdir(exist_ok=True, parents=True)
        return v

    @field_validator("STORE")
    @classmethod
    def generate_store(cls, v: Union[dict[str, dict[str, Any]], Store]) -> Store:
        """Generate the Maggma store."""
        from maggma import stores

        if isinstance(v, dict):
            store_name = next(iter(v.keys()))
            store = getattr(stores, store_name)

            return store(**v[store_name])
        else:
            return v

    @field_validator("ESPRESSO_PARALLEL_CMD")
    @classmethod
    def validate_espresso_parallel_cmd(
        cls, v: Union[str, tuple[str, str]]
    ) -> tuple[str, str]:
        """Clean up Espresso parallel command."""

        if isinstance(v, str):
            v = (v, "")

        return v

    @staticmethod
    def _use_custom_config_settings(settings: dict[str, Any]) -> dict[str, Any]:
        """Parse user settings from a custom YAML.

        Parameters
        ----------
        settings
            Initial settings.

        Returns
        -------
        dict
            Updated settings based on the custom YAML.
        """
        config_file_path = (
            Path(settings.get("CONFIG_FILE", _DEFAULT_CONFIG_FILE_PATH))
            .expanduser()
            .resolve()
        )

        new_settings = {}  # type: dict
        if config_file_path.exists() and config_file_path.stat().st_size > 0:
            new_settings |= loadfn(config_file_path)

        new_settings.update(settings)
        return new_settings

    @model_validator(mode="before")
    @classmethod
    def load_user_settings(cls, settings: dict[str, Any]) -> dict[str, Any]:
        """
        Loads settings from a root file if available and uses that as defaults in place
        of built in defaults. Will also convert common strings to their proper types.

        Parameters
        ----------
        settings
            Settings to load.

        Returns
        -------
        dict
            Loaded settings.
        """
        return _type_handler(cls._use_custom_config_settings(settings))


def _type_handler(settings: dict[str, Any]) -> dict[str, Any]:
    """
    Convert common strings to their proper types.

    Parameters
    ----------
    settings
        Initial settings.

    Returns
    -------
    dict
        Updated settings.
    """
    for key, value in settings.items():
        if isinstance(value, str):
            if value.lower() in {"null", "none"}:
                settings[key] = None
            elif value.lower() in {"true", "false"}:
                settings[key] = value.lower() == "true"

    return settings


@contextmanager
def change_settings(changes: dict[str, Any] | None):
    """
    Temporarily change an attribute of an object.

    Parameters
    ----------
    changes
        Dictionary of changes to make formatted as attribute: value.
    """
    from quacc import _internally_set_settings, get_settings

    settings = get_settings()
    original_values = {attr: getattr(settings, attr) for attr in changes}

    _internally_set_settings(changes=changes)

    try:
        yield
    finally:
        _internally_set_settings(changes=original_values)


def change_settings_wrap(func: Callable, changes: dict[str, Any]) -> Callable:
    """
    Wraps a function with the change_settings context manager if not already wrapped.

    Parameters
    ----------
    func
        The function to wrap.
    changes
        The settings to apply within the context manager.

    Returns
    -------
    Callable
        The wrapped function.
    """
    original_func = func._original_func if getattr(func, "_changed", False) else func

    @wraps(original_func)
    def wrapper(*args, **kwargs):
        with change_settings(changes):
            return original_func(*args, **kwargs)

    wrapper._changed = True
    wrapper._changes = changes
    wrapper._original_func = original_func
    return wrapper


def nest_results_dir_wrap(func: Callable) -> Callable:
    """
    Wraps a function with the change_settings context manager using a nested RESULTS_DIR

    Parameters
    ----------
    func
        The function to wrap.

    Returns
    -------
    Callable
        The wrapped function.
    """
    from quacc import get_settings

    changes = getattr(func, "_changes", {})

    # Get the settings from the calling function's context
    results_parent_dir = get_settings().RESULTS_DIR
    time_now = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M-%S-%f")
    nested_results_dir = results_parent_dir / Path(
        f"{inspect.getmodule(func).__name__}.{func.__name__}-{time_now}-{randint(10000, 99999)}"
    )

    # If someone explcitly set RESULTS_DIR in change_settings already
    # they probably know what they're doing and really want a specific
    # folder!
    if "RESULTS_DIR" not in changes:
        changes["RESULTS_DIR"] = nested_results_dir

    return change_settings_wrap(func, changes)
