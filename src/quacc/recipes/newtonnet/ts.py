"""Transition state recipes for the NewtonNet code."""

from __future__ import annotations

import os
from importlib.util import find_spec
from typing import TYPE_CHECKING

from ase import Atoms
from ase.atoms import Atoms
from ase.io import Trajectory, read, write
from ase.mep.neb import NEBOptimizer
from ase.neb import NEB
from geodesic_interpolate.fileio import write_xyz
from geodesic_interpolate.geodesic import Geodesic
from geodesic_interpolate.interpolation import redistribute
from monty.dev import requires

from quacc import SETTINGS, change_settings, job, strip_decorator
from quacc.recipes.newtonnet.core import _add_stdev_and_hess, freq_job, relax_job
from quacc.runners.ase import run_opt
from quacc.schemas.ase import summarize_opt_run
from quacc.utils.dicts import recursive_dict_merge

has_sella = bool(find_spec("sella"))
has_newtonnet = bool(find_spec("newtonnet"))

try:
    from ase.mep import neb
except ImportError:
    neb = None

if has_sella:
    from sella import IRC, Sella
if has_newtonnet:
    from newtonnet.utils.ase_interface import MLAseCalculator as NewtonNet


if TYPE_CHECKING:
    from typing import Any, Literal

    from ase.optimize.optimize import Optimizer
    from numpy.typing import NDArray

    from quacc.recipes.newtonnet.core import FreqSchema
    from quacc.runners.ase import OptParams
    from quacc.schemas._aliases.ase import OptSchema

    class TSSchema(OptSchema):
        freq_job: FreqSchema | None

    class IRCSchema(OptSchema):
        freq_job: FreqSchema | None

    class QuasiIRCSchema(OptSchema):
        irc_job: IRCSchema
        freq_job: FreqSchema | None


@job
@requires(
    has_newtonnet, "NewtonNet must be installed. Refer to the quacc documentation."
)
@requires(has_sella, "Sella must be installed. Refer to the quacc documentation.")
def ts_job(
    atoms: Atoms,
    use_custom_hessian: bool = False,
    run_freq: bool = True,
    freq_job_kwargs: dict[str, Any] | None = None,
    opt_params: OptParams | None = None,
    **calc_kwargs,
) -> TSSchema:
    """
    Perform a transition state (TS) job using the given atoms object.

    Parameters
    ----------
    atoms
        The atoms object representing the system.
    use_custom_hessian
        Whether to use a custom Hessian matrix.
    run_freq
        Whether to run the frequency job.
    freq_job_kwargs
        Keyword arguments to use for the [quacc.recipes.newtonnet.ts.freq_job][]
    opt_params
        Dictionary of custom kwargs for the optimization process. For a list
        of available keys, refer to [quacc.runners.ase.run_opt][].
    **calc_kwargs
        Dictionary of custom kwargs for the NewtonNet calculator. Set a value to
        `quacc.Remove` to remove a pre-existing key entirely. For a list of available
        keys, refer to the `newtonnet.utils.ase_interface.MLAseCalculator` calculator.

    Returns
    -------
    TSSchema
        Dictionary of results. See the type-hint for the data structure.
    """
    freq_job_kwargs = freq_job_kwargs or {}

    calc_defaults = {
        "model_path": SETTINGS.NEWTONNET_MODEL_PATH,
        "settings_path": SETTINGS.NEWTONNET_CONFIG_PATH,
        "hess_method": "autograd",
    }
    opt_defaults = {
        "optimizer": Sella,
        "optimizer_kwargs": (
            {"diag_every_n": 0, "order": 1} if use_custom_hessian else {"order": 1}
        ),
    }

    calc_flags = recursive_dict_merge(calc_defaults, calc_kwargs)
    opt_flags = recursive_dict_merge(opt_defaults, opt_params)

    atoms.calc = NewtonNet(**calc_flags)

    if use_custom_hessian:
        opt_flags["optimizer_kwargs"]["hessian_function"] = _get_hessian

    atoms.calc = NewtonNet(**calc_flags)

    # Run the TS optimization
    dyn = run_opt(atoms, **opt_flags)
    opt_ts_summary = _add_stdev_and_hess(
        summarize_opt_run(dyn, additional_fields={"name": "NewtonNet TS"})
    )

    # Run a frequency calculation
    freq_summary = (
        strip_decorator(freq_job)(opt_ts_summary["atoms"], **freq_job_kwargs)
        if run_freq
        else None
    )
    opt_ts_summary["freq_job"] = freq_summary

    return opt_ts_summary


@job
@requires(
    has_newtonnet, "NewtonNet must be installed. Refer to the quacc documentation."
)
@requires(has_sella, "Sella must be installed. Refer to the quacc documentation.")
def irc_job(
    atoms: Atoms,
    direction: Literal["forward", "reverse"] = "forward",
    run_freq: bool = True,
    freq_job_kwargs: dict[str, Any] | None = None,
    opt_params: OptParams | None = None,
    **calc_kwargs,
) -> IRCSchema:
    """
    Perform an intrinsic reaction coordinate (IRC) job using the given atoms object.

    Parameters
    ----------
    atoms
        The atoms object representing the system.
    direction
        The direction of the IRC calculation ("forward" or "reverse").
    run_freq
        Whether to run the frequency analysis.
    freq_job_kwargs
        Keyword arguments to use for the [quacc.recipes.newtonnet.ts.freq_job][]
    opt_params
        Dictionary of custom kwargs for the optimization process. For a list
        of available keys, refer to [quacc.runners.ase.run_opt][].
    **calc_kwargs
        Custom kwargs for the NewtonNet calculator. Set a value to
        `quacc.Remove` to remove a pre-existing key entirely. For a list of available
        keys, refer to the `newtonnet.utils.ase_interface.MLAseCalculator` calculator.

    Returns
    -------
    IRCSchema
        A dictionary containing the IRC summary and thermodynamic summary.
        See the type-hint for the data structure.
    """
    freq_job_kwargs = freq_job_kwargs or {}

    calc_defaults = {
        "model_path": SETTINGS.NEWTONNET_MODEL_PATH,
        "settings_path": SETTINGS.NEWTONNET_CONFIG_PATH,
    }
    opt_defaults = {
        "optimizer": IRC,
        "optimizer_kwargs": {"dx": 0.1, "eta": 1e-4, "gamma": 0.4, "keep_going": True},
        "run_kwargs": {"direction": direction},
    }

    calc_flags = recursive_dict_merge(calc_defaults, calc_kwargs)
    opt_flags = recursive_dict_merge(opt_defaults, opt_params)

    # Define calculator
    atoms.calc = NewtonNet(**calc_flags)

    # Run IRC
    with change_settings({"CHECK_CONVERGENCE": False}):
        dyn = run_opt(atoms, **opt_flags)
        opt_irc_summary = _add_stdev_and_hess(
            summarize_opt_run(
                dyn, additional_fields={"name": f"NewtonNet IRC: {direction}"}
            )
        )

    # Run frequency job
    freq_summary = (
        strip_decorator(freq_job)(opt_irc_summary["atoms"], **freq_job_kwargs)
        if run_freq
        else None
    )
    opt_irc_summary["freq_job"] = freq_summary

    return opt_irc_summary


@job
@requires(
    has_newtonnet, "NewtonNet must be installed. Refer to the quacc documentation."
)
@requires(has_sella, "Sella must be installed. Refer to the quacc documentation.")
def quasi_irc_job(
    atoms: Atoms,
    direction: Literal["forward", "reverse"] = "forward",
    run_freq: bool = True,
    irc_job_kwargs: dict[str, Any] | None = None,
    relax_job_kwargs: dict[str, Any] | None = None,
    freq_job_kwargs: dict[str, Any] | None = None,
) -> QuasiIRCSchema:
    """
    Perform a quasi-IRC job using the given atoms object. The initial IRC job by default
    is run with `max_steps: 5`.

    Parameters
    ----------
    atoms
        The atoms object representing the system
    direction
        The direction of the IRC calculation
    run_freq
        Whether to run the frequency analysis
    irc_job_kwargs
        Keyword arguments to use for the [quacc.recipes.newtonnet.ts.irc_job][]
    relax_job_kwargs
        Keyword arguments to use for the [quacc.recipes.newtonnet.core.relax_job][]
    freq_job_kwargs
        Keyword arguments to use for the [quacc.recipes.newtonnet.ts.freq_job][]

    Returns
    -------
    QuasiIRCSchema
        A dictionary containing the IRC summary, optimization summary, and
        thermodynamic summary.
        See the type-hint for the data structure.
    """
    relax_job_kwargs = relax_job_kwargs or {}
    freq_job_kwargs = freq_job_kwargs or {}

    irc_job_defaults = {"max_steps": 5}
    irc_job_kwargs = recursive_dict_merge(irc_job_defaults, irc_job_kwargs)

    # Run IRC
    irc_summary = strip_decorator(irc_job)(
        atoms, direction=direction, run_freq=False, **irc_job_kwargs
    )

    # Run opt
    relax_summary = strip_decorator(relax_job)(irc_summary["atoms"], **relax_job_kwargs)

    # Run frequency
    freq_summary = (
        strip_decorator(freq_job)(relax_summary["atoms"], **freq_job_kwargs)
        if run_freq
        else None
    )
    relax_summary["freq_job"] = freq_summary
    relax_summary["irc_job"] = irc_summary

    return relax_summary


def _get_hessian(atoms: Atoms) -> NDArray:
    """
    Calculate and retrieve the Hessian matrix for the given molecular configuration.

    This function takes an ASE Atoms object representing a molecular
    configuration and uses the NewtonNet machine learning calculator to
    calculate the Hessian matrix. The calculated Hessian matrix is then
    returned.

    Parameters
    ----------
    atoms
        The ASE Atoms object representing the molecular configuration.

    Returns
    -------
    NDArray
        The calculated Hessian matrix, reshaped into a 2D array.
    """
    ml_calculator = NewtonNet(
        model_path=SETTINGS.NEWTONNET_MODEL_PATH,
        settings_path=SETTINGS.NEWTONNET_CONFIG_PATH,
    )
    ml_calculator.calculate(atoms)

    return ml_calculator.results["hessian"].reshape((-1, 3 * len(atoms)))


"""
@job
@requires(NewtonNet, "NewtonNet must be installed. Refer to the quacc documentation.")
def neb_job(
    atoms: Atoms,
    relax_endpoints: bool = True,
    run_geodesic: bool = True,
    run_single_ended: bool = True,
    run_freq: bool = True,
    neb_job_kwargs: dict[str, Any] | None = None,
    relax_job_kwargs: dict[str, Any] | None = None,
    freq_job_kwargs: dict[str, Any] | None = None,
):
    relax_job_kwargs = relax_job_kwargs or {}
    freq_job_kwargs = freq_job_kwargs or {}

    irc_job_defaults = {"max_steps": 5}
    irc_job_kwargs = recursive_dict_merge(irc_job_defaults, irc_job_kwargs)

    # Run IRC
    irc_summary = strip_decorator(irc_job)(
        atoms, direction=direction, run_freq=False, **irc_job_kwargs
    )

    # Run opt
    relax_summary = strip_decorator(relax_job)(irc_summary["atoms"], **relax_job_kwargs)

    # Run frequency
    freq_summary = (
        strip_decorator(freq_job)(relax_summary["atoms"], **freq_job_kwargs)
        if run_freq
        else None
    )
    relax_summary["freq_job"] = freq_summary
    relax_summary["irc_job"] = irc_summary

    return relax_summary
"""


def sella_wrapper(
    atoms_object,
    traj_file=None,
    sella_order=0,
    use_internal=True,
    traj_log_interval=2,
    fmax_cutoff=1e-3,
    max_steps=1000,
):
    if traj_file:
        traj = Trajectory(traj_file, "w", atoms_object)
    qn = Sella(atoms_object, order=sella_order, internal=use_internal)
    if traj_file:
        qn.attach(traj.write, interval=traj_log_interval)
    qn.run(fmax=fmax_cutoff, steps=max_steps)
    if traj_file:
        traj.close()


def geodesic_interpolate_wrapper(
    r_p_atoms: Atoms,
    nimages: int = 17,
    sweep: bool | None = None,
    output: str = "interpolated.xyz",
    tol: float = 2e-3,
    maxiter: int = 15,
    microiter: int = 20,
    scaling: float = 1.7,
    friction: float = 1e-2,
    dist_cutoff: float = 3,
    save_raw: str | None = None,
):
    """
    Interpolates between two geometries and optimizes the path.

    Parameters:
    filename (str): XYZ file containing geometries.
    nimages (int): Number of images. Default is 17.
    sweep (bool): Sweep across the path optimizing one image at a time.
                  Default is to perform sweeping updates if there are more than 35 atoms.
    output (str): Output filename. Default is "interpolated.xyz".
    tol (float): Convergence tolerance. Default is 2e-3.
    maxiter (int): Maximum number of minimization iterations. Default is 15.
    microiter (int): Maximum number of micro iterations for sweeping algorithm. Default is 20.
    scaling (float): Exponential parameter for Morse potential. Default is 1.7.
    friction (float): Size of friction term used to prevent very large change of geometry. Default is 1e-2.
    dist_cutoff (float): Cut-off value for the distance between a pair of atoms to be included in the coordinate system. Default is 3.
    save_raw (str): When specified, save the raw path after bisections but before smoothing. Default is None.
    """
    # Read the initial geometries.
    symbols = r_p_atoms[0].get_chemical_symbols()

    X = [conf.get_positions() for conf in r_p_atoms]

    if len(X) < 2:
        raise ValueError("Need at least two initial geometries.")

    # First redistribute number of images. Perform interpolation if too few and subsampling if too many images are given
    raw = redistribute(symbols, X, nimages, tol=tol * 5)
    if save_raw is not None:
        write_xyz(save_raw, symbols, raw)

    # Perform smoothing by minimizing distance in Cartesian coordinates with redundant internal metric
    # to find the appropriate geodesic curve on the hyperspace.
    smoother = Geodesic(symbols, raw, scaling, threshold=dist_cutoff, friction=friction)
    if sweep is None:
        sweep = len(symbols) > 35
    try:
        if sweep:
            smoother.sweep(tol=tol, max_iter=maxiter, micro_iter=microiter)
        else:
            smoother.smooth(tol=tol, max_iter=maxiter)
    finally:
        # Save the smoothed path to output file. try block is to ensure output is saved if one ^C the process, or there is an error
        write_xyz(output, symbols, smoother.path)
    return symbols, smoother.path


def setup_images(logdir: str, xyz_r_p: str, n_intermediate: int = 40):
    """
    Sets up intermediate images for NEB calculations between reactant and product states.

    Parameters:
    logdir (str): Directory to save the intermediate files.
    xyz_r_p (str): Path to the XYZ file containing reactant and product structures.
    n_intermediate (int): Number of intermediate images to generate.

    Returns:
    List: List of ASE Atoms objects with calculated energies and forces.
    """
    calc_defaults = {
        "model_path": SETTINGS.NEWTONNET_MODEL_PATH,
        "settings_path": SETTINGS.NEWTONNET_CONFIG_PATH,
    }

    calc_flags = recursive_dict_merge(calc_defaults, {})

    try:
        # Ensure the log directory exists
        os.makedirs(logdir, exist_ok=True)

        # Read reactant and product structures
        reactant = read(xyz_r_p, index="0")
        product = read(xyz_r_p, index="1")

        # Optimize reactant and product structures using sella
        for atom, name in zip([reactant, product], ["reactant", "product"]):
            # atom.calc = calc()
            atom.calc = NewtonNet(**calc_flags)
            traj_file = os.path.join(logdir, f"{name}_opt.traj")
            sella_wrapper(atom, traj_file=traj_file, sella_order=0)
        # Save optimized reactant and product structures
        r_p_path = os.path.join(logdir, "r_p.xyz")
        write(r_p_path, [reactant.copy(), product.copy()])

        # Generate intermediate images using geodesic interpolation
        symbols, smoother_path = geodesic_interpolate_wrapper(
            [reactant.copy(), product.copy()]
        )
        images = [Atoms(symbols=symbols, positions=conf) for conf in smoother_path]

        # Calculate energies and forces for each intermediate image
        for image in images:
            # image.calc = calc()
            # ml_calculator = calc()
            image.calc = NewtonNet(**calc_flags)
            ml_calculator = NewtonNet(**calc_flags)
            ml_calculator.calculate(image)

            energy = ml_calculator.results["energy"]
            forces = ml_calculator.results["forces"]

            image.info["energy"] = energy
            image.arrays["forces"] = forces

        # Save the geodesic path
        geodesic_path = os.path.join(logdir, "geodesic_path.xyz")
        write(geodesic_path, images)

        return images

    except Exception:
        return []


def run_neb_method(
    method: str,
    optimizer: Optimizer | None = NEBOptimizer,
    opt_method: str | None = "aseneb",
    precon: str | None = None,
    logdir: str | None = None,
    xyz_r_p: str | None = None,
    n_intermediate: int | None = 20,
    k: float | None = 0.1,
    max_steps: int | None = 1000,
    fmax_cutoff: float | None = 1e-2,
) -> None:
    """
    Run NEB method.

    Args:
        method (str): NEB method.
        optimizer (Optimizer, Optional): NEB path Optimizer function, Defaults to NEBOptimizer.
        precon (str, optional): Preconditioner method. Defaults to None.
        opt_method (str, Optimizer): Optimization method. Defaults to aseneb.
        logdir (str, optional): Directory to save logs. Defaults to None.
        xyz_r_p (str, optional): Path to reactant and product XYZ files. Defaults to None.
        n_intermediate (int, optional): Number of intermediate images. Defaults to 20.
        k (float, optional): force constant for the springs in NEB. Defaults to 0.1.
        max_steps (int, optional): maximum number of optimization steps allowed. Defaults to 1000.
        fmax_cutoff (float: optional): convergence cut-off criteria for the NEB optimization. Defaults to 1e-2.
    """
    images = setup_images(logdir, xyz_r_p, n_intermediate=n_intermediate)

    mep = NEB(
        images,
        k=k,
        method=method,
        climb=True,
        precon=precon,
        remove_rotation_and_translation=True,
        parallel=True,
    )

    os.makedirs(logdir, exist_ok=True)
    log_filename = f"neb_band_{method}_{optimizer.__name__}_{precon}.txt"

    logfile_path = os.path.join(logdir, log_filename)

    opt = optimizer(mep, method=opt_method, logfile=logfile_path, verbose=2)

    opt.run(fmax=fmax_cutoff, steps=max_steps)

    # The following was written because of some error in writing the xyz file below
    images_copy = []
    for image in images:
        image_copy = Atoms(symbols=image.symbols, positions=image.positions)
        image_copy.info["energy"] = image.get_potential_energy()
        images_copy.append(image_copy)

    write(
        f"{logdir}/optimized_path_{method}_{optimizer.__name__}_{precon}.xyz",
        images_copy,
    )
    return images
