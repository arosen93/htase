"""Schemas for VASP."""

from __future__ import annotations

import os
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING

from ase.io import read
from emmet.core.tasks import TaskDoc
from monty.os.path import zpath
from pymatgen.command_line.bader_caller import bader_analysis_from_path
from pymatgen.command_line.chargemol_caller import ChargemolAnalysis

from quacc import QuaccDefault, get_settings
from quacc.atoms.core import get_final_atoms_from_dynamics
from quacc.schemas.ase import Summarize
from quacc.utils.dicts import finalize_dict, recursive_dict_merge

try:
    from pymatgen.io.validation import ValidationDoc
except ImportError:
    ValidationDoc = None

if TYPE_CHECKING:
    from typing import Any

    from ase.atoms import Atoms
    from ase.optimize.optimize import Optimizer
    from emmet.core.base import EmmetBaseModel
    from maggma.core import Store

    from quacc.types import (
        BaderSchema,
        ChargemolSchema,
        DefaultSetting,
        VaspASEOptSchema,
        VaspSchema,
    )

LOGGER = getLogger(__name__)


class VaspSummarize:
    """
    Get tabulated results from a VASP run and store them in a database-friendly format.
    """

    def __init__(
        self,
        directory: str | Path | None = None,
        move_magmoms: bool = True,
        run_bader: bool | DefaultSetting = QuaccDefault,
        run_chargemol: bool | DefaultSetting = QuaccDefault,
        check_convergence: bool | DefaultSetting = QuaccDefault,
        check_mp_compatibility: bool = False,
        additional_fields: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the VASP summarizer.

        Parameters
        ----------
        directory
            Path to VASP outputs. A value of None specifies the calculator directory.
        move_magmoms
            Whether to move the final magmoms of the original Atoms object to the
            initial magmoms of the returned Atoms object.
        run_bader
            Whether a Bader analysis should be performed. Will not run if bader
            executable is not in PATH even if bader is set to True. Defaults to
            VASP_BADER in settings.
        run_chargemol
            Whether a Chargemol analysis should be performed. Will not run if chargemol
            executable is not in PATH even if chargmeol is set to True. Defaults to
            VASP_CHARGEMOL in settings.
        check_convergence
            Whether to throw an error if convergence is not reached. Defaults to True in
            settings.
        check_mp_compatibility
            Whether to check compatibility with the current version of MP.
            Requires `pymatgen-io-validation` to do the check.
        additional_fields
            Additional fields to add to the task document.

        Returns
        -------
        None
        """
        self.directory = directory
        self.move_magmoms = move_magmoms
        self.run_bader = run_bader
        self.run_chargemol = run_chargemol
        self.check_convergence = check_convergence
        self.check_mp_compatibility = check_mp_compatibility
        self.additional_fields = additional_fields or {}
        self._settings = get_settings()

    def run(
        self, final_atoms: Atoms, store: Store | None | DefaultSetting = QuaccDefault
    ) -> VaspSchema:
        """
        Get tabulated results from a VASP run and store them in a database-friendly format.

        Parameters
        ----------
        final_atoms
            ASE Atoms object following a calculation.
        store
            Maggma Store object to store the results in. Defaults to `QuaccSettings.STORE`,

        Returns
        -------
        VaspSchema
            Dictionary representation of the task document
        """
        run_bader = (
            self._settings.VASP_BADER
            if self.run_bader == QuaccDefault
            else self.run_bader
        )
        run_chargemol = (
            self._settings.VASP_CHARGEMOL
            if self.run_chargemol == QuaccDefault
            else self.run_chargemol
        )
        check_convergence = (
            self._settings.CHECK_CONVERGENCE
            if self.check_convergence == QuaccDefault
            else self.check_convergence
        )
        directory = Path(self.directory or final_atoms.calc.directory)
        store = self._settings.STORE if store == QuaccDefault else store
        additional_fields = self.additional_fields or {}

        # Fetch all tabulated results from VASP outputs files. Fortunately, emmet
        # already has a handy function for this
        vasp_task_doc = TaskDoc.from_directory(directory).model_dump()

        # Get MP validation doc
        if self.check_mp_compatibility:
            mp_compat_model = _validate_mp_compatability(directory)
            mp_compat_doc = (
                {"validation": mp_compat_model.model_dump()} if mp_compat_model else {}
            )
        else:
            mp_compat_doc = {}

        # Check for calculation convergence
        if check_convergence and vasp_task_doc["state"] != "successful":
            raise RuntimeError(
                f"VASP calculation did not converge. Will not store task data. Refer to {directory}"
            )

        poscar_path = directory / "POSCAR"
        initial_atoms = read(zpath(str(poscar_path)))
        base_task_doc = Summarize(
            directory=directory,
            move_magmoms=self.move_magmoms,
            additional_fields=self.additional_fields,
        ).run(final_atoms, initial_atoms, store=None)

        if nsteps := len([f for f in os.listdir(directory) if f.startswith("step")]):
            intermediate_vasp_task_docs = {
                "steps": {
                    n: TaskDoc.from_directory(directory / f"step{n}").model_dump()
                    for n in range(nsteps)
                    if (directory / f"step{n}").is_dir()
                }
            }
        else:
            intermediate_vasp_task_docs = {}

        # Get Bader analysis
        if run_bader:
            try:
                bader_results = bader_runner(directory)
            except Exception:
                bader_results = None
                LOGGER.warning("Bader analysis could not be performed.", exc_info=True)

            if bader_results:
                vasp_task_doc["bader"] = bader_results

        # Get the Chargemol analysis
        if run_chargemol:
            try:
                chargemol_results = chargemol_runner(directory)
            except Exception:
                chargemol_results = None
                LOGGER.warning(
                    "Chargemol analysis could not be performed.", exc_info=True
                )

            if chargemol_results:
                vasp_task_doc["chargemol"] = chargemol_results

        # Make task document
        unsorted_task_doc = (
            intermediate_vasp_task_docs
            | vasp_task_doc
            | base_task_doc
            | mp_compat_doc
            | additional_fields
        )
        return finalize_dict(
            unsorted_task_doc,
            directory=directory,
            gzip_file=self._settings.GZIP_FILES,
            store=store,
        )

    def ase_opt(
        self,
        optimizer: Optimizer,
        trajectory: list[Atoms] | None = None,
        store: Store | None | DefaultSetting = QuaccDefault,
    ) -> VaspASEOptSchema:
        """
        Summarize an ASE-based VASP optimization.

        Parameters
        ----------
        optimizer
            The ASE optimizer object
        trajectory
            ASE Trajectory object or list[Atoms] from reading a trajectory file. If
            None, the trajectory must be found in dyn.trajectory.filename.
        store
            Maggma Store object to store the results in. Defaults to `QuaccSettings.STORE`,
        """
        store = self._settings.STORE if store == QuaccDefault else store

        final_atoms = get_final_atoms_from_dynamics(optimizer)
        directory = Path(self.directory or final_atoms.calc.directory)

        opt_run_summary = Summarize(
            directory=directory,
            move_magmoms=self.move_magmoms,
            additional_fields=self.additional_fields,
        ).opt(
            optimizer,
            trajectory=trajectory,
            check_convergence=self.check_convergence,
            store=None,
        )

        vasp_summary = self.run(final_atoms, store=None)
        unsorted_task_doc = recursive_dict_merge(vasp_summary, opt_run_summary)
        return finalize_dict(
            unsorted_task_doc,
            directory=directory,
            gzip_file=self._settings.GZIP_FILES,
            store=store,
        )


def bader_runner(path: Path | str) -> BaderSchema:
    """
    Runs a Bader partial charge and spin moment analysis using the VASP output
    files in the given path. This function requires that `bader` is located in
    your PATH environment variable. See
    http://theory.cm.utexas.edu/henkelman/code/bader for the bader code.

    Parameters
    ----------
    path
        The path where the VASP output files are located. Must include CHGCAR,
        AECCAR0, AECCAR2, and POTCAR files. These files can be gzip'd or not --
        it doesn't matter. If None, the current working directory is used.

    Returns
    -------
    BaderSchema
        Dictionary containing the Bader analysis summary
    """
    # Make sure files are present
    relevant_files = ["AECCAR0", "AECCAR2", "CHGCAR", "POTCAR"]
    for f in relevant_files:
        if not Path(path, f).exists() and not Path(path, f"{f}.gz").exists():
            msg = f"Could not find {f} in {path}."
            raise FileNotFoundError(msg)

    bader_stats = bader_analysis_from_path(path)

    # Store the partial charge, which is much more useful than the raw charge
    # and is more intuitive than the charge transferred. An atom with a positive
    # partial charge is cationic, whereas an atom with a negative partial charge
    # is anionic.
    bader_stats["partial_charges"] = [-c for c in bader_stats["charge_transfer"]]

    # Some cleanup of the returned dictionary
    if "magmom" in bader_stats:
        bader_stats["spin_moments"] = bader_stats["magmom"]
    for k in ["charge", "charge_transfer", "reference_used", "magmom"]:
        bader_stats.pop(k, None)

    return bader_stats


def chargemol_runner(
    path: Path | str, atomic_densities_path: str | None = None
) -> ChargemolSchema:
    """
    Runs a Chargemol (i.e. DDEC6 + CM5) analysis using the VASP output files in
    the given path. This function requires that the chargemol executable, given
    by the name `Chargemol_09_26_2017_linux_parallel`,
    `Chargemol_09_26_2017_linux_serial`, or `chargemol` is in the system PATH
    environment variable. See https://sourceforge.net/projects/ddec/files for
    the Chargemol code.

    Parameters
    ----------
    path
        The path where the VASP output files are located. Must include CHGCAR,
        AECCAR0, AECCAR2, and POTCAR files. These files can be gzip'd or not --
        it doesn't matter. If None, the current working directory is used.
    atomic_densities_path
        The path where the reference atomic densities are located for Chargemol.
        If None, we assume that this directory is defined in an environment
        variable named DDEC6_ATOMIC_DENSITIES_DIR. See the Chargemol
        documentation for more information.

    Returns
    -------
    ChargemolSchema
        Dictionary containing the Chargemol analysis summary
    """
    # Make sure files are present
    relevant_files = ["AECCAR0", "AECCAR2", "CHGCAR", "POTCAR"]
    for f in relevant_files:
        if not Path(path, f).exists() and not Path(path, f"{f}.gz").exists():
            msg = f"Could not find {f} in {path}."
            raise FileNotFoundError(msg)

    # Check environment variable
    if atomic_densities_path is None and "DDEC6_ATOMIC_DENSITIES_DIR" not in os.environ:
        msg = "DDEC6_ATOMIC_DENSITIES_DIR environment variable not defined."
        raise OSError(msg)

    # Run Chargemol analysis
    return ChargemolAnalysis(path=path, atomic_densities_path=atomic_densities_path)


def _validate_mp_compatability(directory: Path | str) -> EmmetBaseModel | None:
    """
    Validate the output of a VASP calculation for Materials Project compatibility.

    Parameters
    ----------
    directory
        Path to the directory containing the VASP calculation.

    Returns
    -------
    EmmetBaseModel | None
        The validation document.
    """
    if ValidationDoc is None:
        LOGGER.debug(
            "pymatgen-io-validation is not installed. Skipping MP compatability check."
        )
        return None
    validation_doc = ValidationDoc.from_directory(dir_name=directory)
    if not validation_doc.valid:
        LOGGER.warning(
            f"Calculation in {directory} is not MP-compatible for the following reasons: {validation_doc.reasons}"
        )
    if validation_doc.warnings:
        LOGGER.warning(
            f"Calculation in {directory} has the following MP-related warnings: {validation_doc.warnings}"
        )
    return validation_doc
