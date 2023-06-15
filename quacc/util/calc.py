"""
Utility functions for running ASE calculators
"""
from __future__ import annotations

import os
from tempfile import mkdtemp
from typing import Literal

import numpy as np
from ase import optimize
from ase.atoms import Atoms
from ase.io import read
from ase.io.trajectory import Trajectory
from ase.optimize.optimize import Optimizer
from ase.vibrations import Vibrations
from monty.os.path import zpath
from monty.shutil import copy_r, gzip_dir

from quacc import SETTINGS
from quacc.util.atoms import copy_atoms
from quacc.util.files import copy_decompress


def run_calc(
    atoms: Atoms,
    geom_file: str | None = None,
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
    scratch_dir
        Path where a tmpdir should be made for running the calculation. If None,
        the current working directory will be used.
    gzip
        Whether to gzip the output files.
    copy_files
        Filenames to copy from source to scratch directory.

    Returns
    -------
    Atoms
        The updated Atoms object,
    """

    if atoms.calc is None:
        raise ValueError("Atoms object must have attached calculator.")
    atoms = copy_atoms(atoms)

    cwd = os.getcwd()
    scratch_dir = scratch_dir or cwd
    symlink = os.path.join(cwd, "tmp_dir")

    if not os.path.exists(scratch_dir):
        os.makedirs(scratch_dir)

    tmpdir = mkdtemp(prefix="quacc-tmp-", dir=scratch_dir)

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
    copy_r(tmpdir, cwd)

    # Remove symlink
    if os.path.islink(symlink):
        os.remove(symlink)

    # Some ASE calculators do not update the atoms object in-place with
    # a call to .get_potential_energy(). This is a workaround to ensure
    # that the atoms object is updated with the correct positions, cell,
    # and magmoms.
    if geom_file and os.path.exists(zpath(geom_file)):
        # Note: We have to be careful to make sure we don't lose the
        # converged magnetic moments, if present. That's why we simply
        # update the positions and cell in-place.
        atoms_new = read(zpath(geom_file))
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

    return atoms


def run_ase_opt(
    atoms: Atoms,
    fmax: float = 0.01,
    max_steps: int = 500,
    optimizer: Literal[
        "Berny",
        "BFGS",
        "BFGSLineSearch",
        "FIRE",
        "GPMin",
        "LBFGS",
        "LBFGSLineSearch",
        "MDMin",
        "QuasiNewton",
        "Sella",
        "SellaIRC",
    ] = "FIRE",
    optimizer_kwargs: dict | None = None,
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
        Name of optimizer class to use.
    optimizer_kwargs
        Dictionary of kwargs for the optimizer.
    scratch_dir
        Path where a tmpdir should be made for running the calculation. If None,
        the current working directory will be used.
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
    scratch_dir = scratch_dir or cwd
    symlink = os.path.join(cwd, "tmp_dir")
    optimizer_kwargs = optimizer_kwargs or {}

    if not os.path.exists(scratch_dir):
        os.makedirs(scratch_dir)

    if "trajectory" not in optimizer_kwargs:
        optimizer_kwargs["trajectory"] = Trajectory("opt.traj", "w")

    # Get optimizer
    if optimizer.lower() in {"sella", "sellairc"}:
        if not atoms.pbc.any() and "internal" not in optimizer_kwargs:
            optimizer_kwargs["internal"] = True
        try:
            from sella import IRC, Sella
        except ImportError as e:
            raise ImportError(
                "You must install Sella to use Sella optimizers. Try `pip install sella`."
            ) from e

    if optimizer.lower() == "sella":
        opt_class = Sella
    elif optimizer.lower() == "sellairc":
        opt_class = IRC
    else:
        try:
            opt_class = getattr(optimize, optimizer)
        except AttributeError as e:
            raise ValueError(
                f"Unknown {optimizer=}, must be one of {list(dir(optimize))} or Sella, SellaIRC"
            ) from e

    tmpdir = mkdtemp(prefix="quacc-tmp-", dir=scratch_dir)

    if os.name != "nt":
        if os.path.islink(symlink):
            os.unlink(symlink)
        os.symlink(tmpdir, symlink)

    # Copy files to scratch and decompress them if needed
    if copy_files:
        copy_decompress(copy_files, tmpdir)

    # Define optimizer class
    dyn = opt_class(atoms, **optimizer_kwargs)

    # Run calculation
    os.chdir(tmpdir)
    dyn.run(fmax=fmax, steps=max_steps)
    os.chdir(cwd)

    # Gzip files in tmpdir
    if gzip:
        gzip_dir(tmpdir)

    # Copy files back to run_dir
    copy_r(tmpdir, cwd)

    # Remove symlink
    if os.path.islink(symlink):
        os.remove(symlink)

    return dyn


def run_ase_vib(
    atoms: Atoms,
    vib_kwargs: dict | None = None,
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
    scratch_dir
        Path where a tmpdir should be made for running the calculation. If None,
        the current working directory will be used.
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
    scratch_dir = scratch_dir or cwd
    symlink = os.path.join(cwd, "tmp_dir")
    vib_kwargs = vib_kwargs or {}

    if not os.path.exists(scratch_dir):
        os.makedirs(scratch_dir)

    tmpdir = mkdtemp(prefix="quacc-tmp-", dir=scratch_dir)

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
    copy_r(tmpdir, cwd)

    # Remove symlink
    if os.path.islink(symlink):
        os.remove(symlink)

    return vib
