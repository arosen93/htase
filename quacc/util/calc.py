import os
from copy import deepcopy
from shutil import copy, copyfileobj
from tempfile import TemporaryDirectory
from ase.atoms import Atoms
import warnings


def run_calc(
    atoms: Atoms, run_dir: str = None, scratch_dir: str = None, gzip: bool = False
) -> float:
    """
    Run a calculation in a scratch directory and copy the results back to the
    original directory. This can be useful if file I/O is slow in the working
    directory, so long as file transfer speeds are reasonable.

    This is a wrapper around atoms.get_potential_energy().

    Parameters
    ----------
    atoms : .Atoms
        The Atoms object to run the calculation on.
    run_dir : str
        Path to the directory containing the calculation to be run.
        If None, the current working directory will be used.
    scratch_dir : str
        Path to the base directory to store the scratch temp directories.
        If None, a temporary directory in $SCRATCH will be used. If $SCRATCH
        is not present, everything will be run in run_dir.
    gzip : bool
        Whether to gzip the output files.

    Returns
    -------
    .Atoms
        The updated .Atoms object,
    """

    atoms = deepcopy(atoms)

    # Find the relevant paths
    if not run_dir:
        run_dir = os.getcwd()
    if not scratch_dir:
        if "SCRATCH" in os.environ:
            scratch_dir = os.path.expandvars("$SCRATCH")
        else:
            warnings.warn(
                "scratch_path is None yet $SCRATCH environment variable is not set. No scratch directory will be used."
            )
            scratch_dir = run_dir

    with TemporaryDirectory(dir=scratch_dir, prefix="quacc-") as scratch_path:

        # Copy files from working directory to scratch directory
        for f in os.listdir(run_dir):
            copy(os.path.join(run_dir, f), os.path.join(scratch_path, f))

        # Leave a note in the run directory for where the scratch is located in case
        # the job dies partway through
        scratch_path_note = os.path.join(run_dir, "scratch_path.txt")
        with open(scratch_path_note, "w") as f:
            f.write(scratch_path)

        # Run calculation via get_potential_energy()
        os.chdir(scratch_path)
        e = atoms.get_potential_energy()
        os.chdir(run_dir)

        # Copy files from scratch directory to working directory
        for f in os.listdir(scratch_path):
            # gzip the files in scratch before copying them back
            if gzip:
                with open(os.path.join(scratch_path, f), "rb") as f_in:
                    with gzip.open(os.path.join(run_dir, f + ".gz"), "wb") as f_out:
                        copyfileobj(f_in, f_out)
            else:
                copy(os.path.join(scratch_path, f), os.path.join(run_dir, f))

    # Remove the scratch note
    if os.path.exists(scratch_path_note):
        os.remove(scratch_path_note)

    return atoms
