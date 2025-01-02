"""
Materials Project-compatible recipes.

!!! Important

    Be careful to use Materials Project-compatible pseudpotential versions!

    Legacy (GGA): use the original (no version) PAW PBE potentials.

    Legacy (Meta-GGA): use the v.54 PAW PBE potentials.

    2024 workflows: v.64 PAW PBE potentials.

!!! Note

    When using these workflows, please cite the following papers:

    Legacy (GGA): https://doi.org/10.1063/1.4812323.

    Legacy (Meta-GGA): https://doi.org/10.1103/PhysRevMaterials.6.013801.

    2024 workflows: Coming soon.
"""

from __future__ import annotations

from importlib.util import find_spec
from typing import TYPE_CHECKING

from monty.dev import requires

from quacc import change_settings, flow, job
from quacc.calculators.vasp.params import MPtoASEParams
from quacc.recipes.vasp._base import run_and_summarize
from quacc.wflow_tools.customizers import customize_funcs

if TYPE_CHECKING:
    from collections.abc import Callable

    from ase.atoms import Atoms

    from quacc.types import MPRelaxFlowSchema, SourceDirectory, VaspSchema

has_atomate2 = bool(find_spec("atomate2"))
if has_atomate2:
    from typing import Any, Literal

    from atomate2.vasp.jobs.mp import (
        MPGGARelaxMaker,
        MPGGAStaticMaker,
        MPMetaGGARelaxMaker,
        MPMetaGGAStaticMaker,
        MPPreRelaxMaker,
    )
    from atomate2.vasp.jobs.mp24 import (
        MP24GGAPreRelaxMaker,
        MP24GGARelaxMaker,
        MP24GGAStaticMaker,
        MP24MetaGGAPreRelaxMaker,
        MP24MetaGGARelaxMaker,
        MP24MetaGGAStaticMaker,
    )


_MP_SETTINGS = {"VASP_INCAR_COPILOT": "off", "VASP_USE_CUSTODIAN": True}


@job
@requires(has_atomate2, "atomate2 is not installed. Run `pip install quacc[mp]`")
def mp_pre_relax_job(
    atoms: Atoms,
    method: Literal["gga", "metagga"] = "gga",
    version: Literal["legacy", "mp24"] = "mp24",
    prev_dir: SourceDirectory | None = None,
    **calc_kwargs,
) -> VaspSchema:
    """
    Function to pre-relax a structure with the Materials Project settings.

    Parameters
    ----------
    atoms
        Atoms object
    method
        Whether GGA or Meta-GGA compatability is desired. Note that for the
        pre-relax step with "metagga", this is still a GGA (PBEsol) functional.
    version
        The version of the Materials Project settings to use.
    prev_dir
        A previous directory for a prior step in the workflow.
    **calc_kwargs
        Custom kwargs for the Vasp calculator. Set a value to
        `None` to remove a pre-existing key entirely. For a list of available
        keys, refer to [quacc.calculators.vasp.vasp.Vasp][].

    Returns
    -------
    VaspSchema
        Dictionary of results.
    """
    if version == "legacy":
        vasp_maker = MPGGARelaxMaker if method.lower() == "gga" else MPPreRelaxMaker
    else:
        vasp_maker = (
            MP24GGAPreRelaxMaker
            if method.lower() == "gga"
            else MP24MetaGGAPreRelaxMaker
        )
    calc_defaults = MPtoASEParams(atoms=atoms, prev_dir=prev_dir).convert_vasp_maker(
        vasp_maker
    )
    with change_settings(_MP_SETTINGS):
        return run_and_summarize(
            atoms,
            calc_defaults=calc_defaults,
            calc_swaps=calc_kwargs,
            check_mp_compatibility=(version == "mp24"),
            additional_fields={"name": vasp_maker.name},
            copy_files={prev_dir: ["CHGCAR*", "WAVECAR*"]},
        )


@job
@requires(has_atomate2, "atomate2 is not installed. Run `pip install quacc[mp]`")
def mp_relax_job(
    atoms: Atoms,
    method: Literal["gga", "metagga"] = "gga",
    version: Literal["legacy", "mp24"] = "mp24",
    prev_dir: SourceDirectory | None = None,
    **calc_kwargs,
) -> VaspSchema:
    """
    Function to relax a structure with the Materials Project settings.

    Parameters
    ----------
    atoms
        Atoms object
    method
        Whether GGA or Meta-GGA compatability is desired.
    version
        The version of the Materials Project settings to use.
    prev_dir
        A previous directory for a prior step in the workflow.
    **calc_kwargs
        Custom kwargs for the Vasp calculator. Set a value to
        `None` to remove a pre-existing key entirely. For a list of available
        keys, refer to [quacc.calculators.vasp.vasp.Vasp][].

    Returns
    -------
    VaspSchema
        Dictionary of results from [quacc.schemas.vasp.VaspSummarize.run][].
    """
    if version == "legacy":
        vasp_maker = MPGGARelaxMaker if method.lower() == "gga" else MPMetaGGARelaxMaker
    else:
        vasp_maker = (
            MP24GGARelaxMaker if method.lower() == "gga" else MP24MetaGGARelaxMaker
        )
    calc_defaults = MPtoASEParams(atoms=atoms, prev_dir=prev_dir).convert_vasp_maker(
        vasp_maker
    )
    with change_settings(_MP_SETTINGS):
        return run_and_summarize(
            atoms,
            calc_defaults=calc_defaults,
            calc_swaps=calc_kwargs,
            check_mp_compatibility=(version == "mp24"),
            additional_fields={"name": vasp_maker.name},
            copy_files={prev_dir: ["CHGCAR*", "WAVECAR*"]},
        )


@job
@requires(has_atomate2, "atomate2 is not installed. Run `pip install quacc[mp]`")
def mp_static_job(
    atoms: Atoms,
    method: Literal["gga", "metagga"] = "gga",
    version: Literal["legacy", "mp24"] = "mp24",
    prev_dir: SourceDirectory | None = None,
    **calc_kwargs,
) -> VaspSchema:
    """
    Function to run a static calculation on a structure with the Materials Project settings.

    Parameters
    ----------
    atoms
        Atoms object
    method
        Whether GGA or Meta-GGA compatability is desired.
    version
        The version of the Materials Project settings to use.
    prev_dir
        A previous directory for a prior step in the workflow.
    **calc_kwargs
        Custom kwargs for the Vasp calculator. Set a value to
        `None` to remove a pre-existing key entirely. For a list of available
        keys, refer to [quacc.calculators.vasp.vasp.Vasp][].

    Returns
    -------
    VaspSchema
        Dictionary of results from [quacc.schemas.vasp.VaspSummarize.run][].
        See the type-hint for the data structure.
    """
    if version == "legacy":
        vasp_maker = (
            MPGGAStaticMaker if method.lower() == "gga" else MPMetaGGAStaticMaker
        )
    else:
        vasp_maker = (
            MP24GGAStaticMaker if method.lower() == "gga" else MP24MetaGGAStaticMaker
        )
    calc_defaults = MPtoASEParams(atoms=atoms, prev_dir=prev_dir).convert_vasp_maker(
        vasp_maker
    )
    with change_settings(_MP_SETTINGS):
        return run_and_summarize(
            atoms,
            calc_defaults=calc_defaults,
            calc_swaps=calc_kwargs,
            check_mp_compatibility=(version == "mp24"),
            additional_fields={"name": vasp_maker.name},
            copy_files={prev_dir: ["CHGCAR*", "WAVECAR*"]},
        )


@flow
@requires(has_atomate2, "atomate2 is not installed. Run `pip install quacc[mp]`")
def mp_relax_flow(
    atoms: Atoms,
    method: Literal["gga", "metagga"] = "gga",
    version: Literal["legacy", "mp24"] = "legacy",
    job_params: dict[str, dict[str, Any]] | None = None,
    job_decorators: dict[str, Callable | None] | None = None,
) -> MPRelaxFlowSchema:
    """
    Materials Project relaxation and static workflow consisting of:

    1. MP-compatible pre-relax
        - name: "mp_pre_relax_job"
        - job: [quacc.recipes.vasp.mp.mp_pre_relax_job][]

    2. MP-compatible relax
        - name: "mp_relax_job"
        - job: [quacc.recipes.vasp.mp.mp_relax_job][]

    3. MP-compatible static
        - name: "mp_static_job"
        - job: [quacc.recipes.vasp.mp.mp_static_job][]

    Parameters
    ----------
    atoms
        Atoms object for the structure.
    method
        Whether GGA or Meta-GGA compatability is desired.
    version
        The version of the Materials Project settings to use.
    job_params
        Custom parameters to pass to each Job in the Flow. This is a dictionary where
        the keys are the names of the jobs and the values are dictionaries of parameters.
    job_decorators
        Custom decorators to apply to each Job in the Flow. This is a dictionary where
        the keys are the names of the jobs and the values are decorators.

    Returns
    -------
    MPRelaxFlowSchema
        Dictionary of results. See the type-hint for the data structure.
    """
    job_param_defaults = {"all": {"method": method, "version": version}}
    (mp_pre_relax_job_, mp_relax_job_, mp_static_job_) = customize_funcs(
        ["mp_pre_relax_job", "mp_relax_job", "mp_static_job"],
        [mp_pre_relax_job, mp_relax_job, mp_static_job],
        param_defaults=job_param_defaults,
        param_swaps=job_params,
        decorators=job_decorators,
    )

    # Run the pre-relax
    pre_relax_results = mp_pre_relax_job_(atoms)

    # Run the second relax
    relax_results = mp_relax_job_(
        pre_relax_results["atoms"], prev_dir=pre_relax_results["dir_name"]
    )

    # Run the static
    static_results = mp_static_job_(
        relax_results["atoms"], prev_dir=relax_results["dir_name"]
    )

    return {
        "pre_relax": pre_relax_results,
        "relax": relax_results,
        "static": static_results,
    }
