"""Utility functions for running ASE calculators"""
from __future__ import annotations

import os
from shutil import rmtree
from tempfile import mkdtemp

import numpy as np
from ase import Atoms
from ase.io import Trajectory, read
from ase.optimize import FIRE
from ase.optimize.optimize import Optimizer
from ase.vibrations import Vibrations
from monty.os.path import zpath
from monty.shutil import copy_r, gzip_dir

from quacc import SETTINGS
from quacc.util.atoms import copy_atoms
from quacc.util.files import copy_decompress, make_job_dir


def run_calc(
    atoms: Atoms,
    geom_file: str | None = None,
    create_unique_workdir: str = SETTINGS.CREATE_UNIQUE_WORKDIR,
    scratch_dir: str = SETTINGS.SCRATCH_DIR,
    gzip: bool = SETTINGS.GZIP_FILES,
    copy_files: list[str] | None = None,
) -> Atoms:
    """
    Run a calculation in a scratch directory and copy the results back to the
    original directory. This can be useful if file I/O is slow in the working
    directory, so long as file transfer speeds are reasonable.

    This is a wrapper around atoms.get_potential_energy(). Note: This
    function does not modify the atoms object in-place.

    Parameters
    ----------
    atoms
        The Atoms object to run the calculation on.
    geom_file
        The filename of the log file that contains the output geometry, used
        to update the atoms object's positions and cell after a job. It is better
        to specify this rather than relying on ASE's atoms.get_potential_energy()
        function to update the positions, as this varies between codes.
    create_unique_workdir
        Whether to automatically create a unique working directory for each calculation.
    scratch_dir
        Path where a tmpdir should be made for running the calculation. If None,
        the working directory will be used.
    gzip
        Whether to gzip the output files.
    copy_files
        Filenames to copy from source to scratch directory.

    Returns
    -------
    Atoms
        The updated Atoms object.
    """

    if atoms.calc is None:
        raise ValueError("Atoms object must have attached calculator.")
    atoms = copy_atoms(atoms)

    cwd = os.getcwd()

    # Set where to store the results
    job_dir = make_job_dir() if create_unique_workdir else cwd

    # Set where to run the calculation
    scratch_dir = scratch_dir or job_dir

    if not os.path.exists(scratch_dir):
        os.makedirs(scratch_dir)

    tmpdir = os.path.abspath(mkdtemp(prefix="quacc-tmp-", dir=scratch_dir))
    symlink = os.path.join(job_dir, f"{os.path.basename(tmpdir)}-symlink")

    if os.name != "nt":
        if os.path.islink(symlink):
            os.unlink(symlink)
        os.symlink(tmpdir, symlink)

    # Copy files to scratch and decompress them if needed
    if copy_files:
        copy_decompress(copy_files, tmpdir)

    # Run calculation via get_potential_energy()
    os.chdir(tmpdir)
    atoms.get_potential_energy()
    os.chdir(cwd)

    # Gzip files in tmpdir
    if gzip:
        gzip_dir(tmpdir)

    # Copy files back to run_dir
    copy_r(tmpdir, job_dir)

    # Most ASE calculators do not update the atoms object in-place with
    # a call to .get_potential_energy(). This section is done to ensure
    # that the atoms object is updated with the correct positions and cell
    # if a `geom_file` is provided.
    if geom_file and os.path.exists(os.path.join(job_dir, zpath(geom_file))):
        # Note: We have to be careful to make sure we don't lose the
        # converged magnetic moments, if present. That's why we simply
        # update the positions and cell in-place.
        atoms_new = read(os.path.join(job_dir, zpath(geom_file)))
        if isinstance(atoms_new, list):
            atoms_new = atoms_new[-1]

        # Make sure the atom indices didn't get updated somehow (sanity check)
        if (
            np.array_equal(atoms_new.get_atomic_numbers(), atoms.get_atomic_numbers())
            is False
        ):
            raise ValueError("Atomic numbers do not match between atoms and geom_file.")

        atoms.positions = atoms_new.positions
        atoms.cell = atoms_new.cell

    # Remove symlink
    if os.path.islink(symlink):
        os.remove(symlink)

    # Remove the tmpdir
    rmtree(tmpdir)

    return atoms


def run_ase_opt(
    atoms: Atoms,
    fmax: float = 0.01,
    max_steps: int = 500,
    optimizer: Optimizer = FIRE,
    optimizer_kwargs: dict | None = None,
    create_unique_workdir: str = SETTINGS.CREATE_UNIQUE_WORKDIR,
    scratch_dir: str = SETTINGS.SCRATCH_DIR,
    gzip: bool = SETTINGS.GZIP_FILES,
    copy_files: list[str] | None = None,
) -> Optimizer:
    """
    Run an ASE-based optimization in a scratch directory and copy the results
    back to the original directory. This can be useful if file I/O is slow in
    the working directory, so long as file transfer speeds are reasonable.

    This is a wrapper around the optimizers in ASE. Note: This function does
    not modify the atoms object in-place.

    Parameters
    ----------
    atoms
        The Atoms object to run the calculation on.
    fmax
        Tolerance for the force convergence (in eV/A).
    max_steps
        Maximum number of steps to take.
    optimizer
        Optimizer class to use.
    optimizer_kwargs
        Dictionary of kwargs for the optimizer.
    create_unique_workdir
        Whether to automatically create a unique working directory for each calculation.
    scratch_dir
        Path where a tmpdir should be made for running the calculation. If None,
        the working directory will be used.
    gzip
        Whether to gzip the output files.
    copy_files
        Filenames to copy from source to scratch directory.

    Returns
    -------
    Optimizer
        The ASE Optimizer object.
    """

    if atoms.calc is None:
        raise ValueError("Atoms object must have attached calculator.")
    atoms = copy_atoms(atoms)

    cwd = os.getcwd()
    job_dir = make_job_dir() if create_unique_workdir else cwd
    scratch_dir = scratch_dir or job_dir
    optimizer_kwargs = optimizer_kwargs or {}

    if not os.path.exists(scratch_dir):
        os.makedirs(scratch_dir)

    # Set Sella kwargs
    if (
        optimizer.__name__ == "Sella"
        and not atoms.pbc.any()
        and "internal" not in optimizer_kwargs
    ):
        optimizer_kwargs["internal"] = True

    tmpdir = os.path.abspath(mkdtemp(prefix="quacc-tmp-", dir=scratch_dir))
    symlink = os.path.join(job_dir, f"{os.path.basename(tmpdir)}-symlink")

    if os.name != "nt":
        if os.path.islink(symlink):
            os.unlink(symlink)
        os.symlink(tmpdir, symlink)

    # Copy files to scratch and decompress them if needed
    if copy_files:
        copy_decompress(copy_files, tmpdir)

    # Get trajectory filename
    if "trajectory" in optimizer_kwargs:
        if not isinstance(optimizer_kwargs["trajectory"], str):
            raise ValueError("`trajectory` kwarg must be a string.")
        traj_filename = optimizer_kwargs["trajectory"]
    else:
        traj_filename = "opt.traj"

    os.chdir(tmpdir)

    # Set up trajectory
    traj = Trajectory(traj_filename, "w", atoms=atoms)
    optimizer_kwargs["trajectory"] = traj

    # Define optimizer class
    dyn = optimizer(atoms, **optimizer_kwargs)

    # Run calculation
    dyn.run(fmax=fmax, steps=max_steps)

    # Store the trajectory atoms
    dyn.traj_atoms = read(traj_filename, index=":")

    os.chdir(cwd)

    # Gzip files in tmpdir
    if gzip:
        gzip_dir(tmpdir)

    # Copy files back to run_dir
    copy_r(tmpdir, job_dir)

    # Remove symlink
    if os.path.islink(symlink):
        os.remove(symlink)

    # Remove the tmpdir
    rmtree(tmpdir)

    return dyn


def run_ase_vib(
    atoms: Atoms,
    vib_kwargs: dict | None = None,
    create_unique_workdir: str = SETTINGS.CREATE_UNIQUE_WORKDIR,
    scratch_dir: str = SETTINGS.SCRATCH_DIR,
    gzip: bool = SETTINGS.GZIP_FILES,
    copy_files: list[str] | None = None,
) -> Vibrations:
    """
    Run an ASE-based vibration analysis in a scratch directory and copy the results
    back to the original directory. This can be useful if file I/O is slow in
    the working directory, so long as file transfer speeds are reasonable.

    This is a wrapper around the vibrations module in ASE. Note: This function does
    not modify the atoms object in-place.

    Parameters
    ----------
    atoms
        The Atoms object to run the calculation on.
    vib_kwargs
        Dictionary of kwargs for the vibration analysis.
    create_unique_workdir
        Whether to automatically create a unique working directory for each calculation.
    scratch_dir
        Path where a tmpdir should be made for running the calculation. If None,
        the working directory will be used.
    gzip
        Whether to gzip the output files.
    copy_files
        Filenames to copy from source to scratch directory.

    Returns
    -------
    Vibrations
        The updated Vibrations module
    """

    if atoms.calc is None:
        raise ValueError("Atoms object must have attached calculator.")
    atoms = copy_atoms(atoms)

    cwd = os.getcwd()
    job_dir = make_job_dir() if create_unique_workdir else cwd
    scratch_dir = scratch_dir or job_dir
    vib_kwargs = vib_kwargs or {}

    if not os.path.exists(scratch_dir):
        os.makedirs(scratch_dir)

    tmpdir = os.path.abspath(mkdtemp(prefix="quacc-tmp-", dir=scratch_dir))
    symlink = os.path.join(job_dir, f"{os.path.basename(tmpdir)}-symlink")

    if os.name != "nt":
        if os.path.islink(symlink):
            os.unlink(symlink)
        os.symlink(tmpdir, symlink)

    # Copy files to scratch and decompress them if needed
    if copy_files:
        copy_decompress(copy_files, tmpdir)

    # Run calculation
    os.chdir(tmpdir)
    vib = Vibrations(atoms, **vib_kwargs)
    vib.run()
    vib.summary(log="vib_summary.log")
    os.chdir(cwd)

    # Gzip files in tmpdir
    if gzip:
        gzip_dir(tmpdir)

    # Copy files back to run_dir
    copy_r(tmpdir, job_dir)

    # Remove symlink
    if os.path.islink(symlink):
        os.remove(symlink)

    # Remove the tmpdir
    rmtree(tmpdir)

    return vib
