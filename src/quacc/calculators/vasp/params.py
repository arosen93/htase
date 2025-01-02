"""Parameter-related utilities for the Vasp calculator."""

from __future__ import annotations

from importlib.util import find_spec
from logging import getLogger
from typing import TYPE_CHECKING

import numpy as np
from ase.calculators.vasp import Vasp as Vasp_
from monty.dev import requires
from pymatgen.io.ase import AseAtomsAdaptor

from quacc.atoms.core import check_is_metal
from quacc.utils.dicts import sort_dict
from quacc.utils.kpts import convert_pmg_kpts

has_atomate2 = bool(find_spec("atomate2"))

if TYPE_CHECKING:
    from typing import Any, Literal

    from ase.atoms import Atoms
    from pymatgen.io.vasp.sets import DictSet

    from quacc.types import PmgKpts, SourceDirectory

    if has_atomate2:
        from atomate2.vasp.jobs.base import BaseVaspMaker

LOGGER = getLogger(__name__)


def get_param_swaps(
    user_calc_params: dict[str, Any],
    pmg_kpts: dict[Literal["line_density", "kppvol", "kppa"], float],
    input_atoms: Atoms,
    incar_copilot: Literal["off", "on", "aggressive"],
) -> dict[str, Any]:
    """
    Swaps out bad INCAR flags.

    Parameters
    ----------
    user_calc_params
        The user-provided calculator parameters.
    pmg_kpts
        The pmg_kpts kwarg.
    input_atoms
        The input atoms.
    incar_copilot
        INCAR copilot mode. See `quacc.calculators.vasp.vasp.Vasp` for more info.

    Returns
    -------
    dict
        The updated user-provided calculator parameters.
    """
    is_metal = check_is_metal(input_atoms)
    calc = Vasp_(**user_calc_params)
    max_Z = input_atoms.get_atomic_numbers().max()

    if (
        not calc.int_params["lmaxmix"] or calc.int_params["lmaxmix"] < 6
    ) and max_Z > 56:
        LOGGER.info("Recommending LMAXMIX = 6 because you have f electrons.")
        calc.set(lmaxmix=6)
    elif (
        not calc.int_params["lmaxmix"] or calc.int_params["lmaxmix"] < 4
    ) and max_Z > 20:
        LOGGER.info("Recommending LMAXMIX = 4 because you have d electrons.")
        calc.set(lmaxmix=4)

    if (
        calc.bool_params["luse_vdw"]
        or calc.bool_params["lhfcalc"]
        or calc.bool_params["ldau"]
        or calc.dict_params["ldau_luj"]
        or calc.string_params["metagga"]
    ) and not calc.bool_params["lasph"]:
        LOGGER.info(
            "Recommending LASPH = True because you have a +U, vdW, meta-GGA, or hybrid calculation."
        )
        calc.set(lasph=True)

    if calc.string_params["metagga"] and (
        not calc.string_params["algo"] or calc.string_params["algo"].lower() != "all"
    ):
        LOGGER.info("Recommending ALGO = All because you have a meta-GGA calculation.")
        calc.set(algo="all")

    if calc.bool_params["lhfcalc"] and (
        not calc.string_params["algo"]
        or calc.string_params["algo"].lower() not in ["all", "damped", "normal"]
    ):
        LOGGER.info("Recommending ALGO = Normal because you have a hybrid calculation.")
        calc.set(algo="normal")

    if (
        is_metal
        and (calc.int_params["ismear"] and calc.int_params["ismear"] < 0)
        and (calc.int_params["nsw"] and calc.int_params["nsw"] > 0)
    ):
        LOGGER.info(
            "Recommending ISMEAR = 1 and SIGMA = 0.1 because you are likely relaxing a metal."
        )
        calc.set(ismear=1, sigma=0.1)

    if (
        calc.int_params["ismear"] != -5
        and calc.int_params["nsw"] in (None, 0)
        and (
            np.prod(calc.kpts) >= 4
            or (calc.float_params["kspacing"] and calc.float_params["kspacing"] <= 0.5)
        )
    ):
        LOGGER.info("Recommending ISMEAR = -5 because you have a static calculation.")
        calc.set(ismear=-5)

    if (
        calc.int_params["ismear"] == -5
        and np.prod(calc.kpts) < 4
        and calc.float_params["kspacing"] is None
    ):
        LOGGER.info(
            "Recommending ISMEAR = 0 because you don't have enough k-points for ISMEAR = -5."
        )
        calc.set(ismear=0)

    if (
        calc.float_params["kspacing"]
        and calc.float_params["kspacing"] > 0.5
        and calc.int_params["ismear"] == -5
    ):
        LOGGER.info(
            "Recocmmending ISMEAR = 0 because KSPACING is likely too large for ISMEAR = -5."
        )
        calc.set(ismear=0)

    if pmg_kpts and pmg_kpts.get("line_density") and calc.int_params["ismear"] != 0:
        LOGGER.info(
            "Recommending ISMEAR = 0 and SIGMA = 0.01 because you are doing a line mode calculation."
        )
        calc.set(ismear=0, sigma=0.01)

    if calc.int_params["ismear"] == 0 and (
        not calc.float_params["sigma"] or calc.float_params["sigma"] > 0.05
    ):
        LOGGER.info(
            "Recommending SIGMA = 0.05 because ISMEAR = 0 was requested with SIGMA > 0.05."
        )
        calc.set(sigma=0.05)

    if (
        calc.int_params["nsw"]
        and calc.int_params["nsw"] > 0
        and calc.bool_params["laechg"]
    ):
        LOGGER.info(
            "Recommending LAECHG = False because you have NSW > 0. LAECHG is not compatible with NSW > 0."
        )
        calc.set(laechg=False)

    if calc.int_params["ldauprint"] in (None, 0) and (
        calc.bool_params["ldau"] or calc.dict_params["ldau_luj"]
    ):
        LOGGER.info("Recommending LDAUPRINT = 1 because LDAU = True.")
        calc.set(ldauprint=1)

    if calc.special_params["lreal"] and len(input_atoms) < 30:
        LOGGER.info(
            "Recommending LREAL = False because you have a small system (< 30 atoms/cell)."
        )
        calc.set(lreal=False)

    if not calc.int_params["lorbit"] and (
        calc.int_params["ispin"] == 2
        or np.any(input_atoms.get_initial_magnetic_moments() != 0)
    ):
        LOGGER.info(
            "Recommending LORBIT = 11 because you have a spin-polarized calculation."
        )
        calc.set(lorbit=11)

    if (
        (calc.int_params["ncore"] and calc.int_params["ncore"] > 1)
        or (calc.int_params["npar"] and calc.int_params["npar"] > 1)
    ) and (
        calc.bool_params["lhfcalc"] is True
        or calc.bool_params["lrpa"] is True
        or calc.bool_params["lepsilon"] is True
        or calc.int_params["ibrion"] in [5, 6, 7, 8]
    ):
        LOGGER.info(
            "Recommending NCORE = 1 because NCORE/NPAR is not compatible with this job type."
        )
        calc.set(ncore=1, npar=None)

    if (
        calc.int_params["kpar"]
        and calc.int_params["kpar"] > np.prod(calc.kpts)
        and calc.float_params["kspacing"] is None
    ):
        LOGGER.info(
            "Recommending KPAR = 1 because you have too few k-points to parallelize."
        )
        calc.set(kpar=1)

    if calc.bool_params["lhfcalc"] is True and calc.int_params["isym"] in (1, 2):
        LOGGER.info(
            "Recommending ISYM = 3 because you are running a hybrid calculation."
        )
        calc.set(isym=3)

    if calc.bool_params["lsorbit"]:
        LOGGER.info(
            "Recommending ISYM = -1 because you are running an SOC calculation."
        )
        calc.set(isym=-1)

    if (
        (calc.int_params["ncore"] and calc.int_params["ncore"] > 1)
        or (calc.int_params["npar"] and calc.int_params["npar"] > 1)
    ) and (calc.bool_params["lelf"] is True):
        LOGGER.info(
            "Recommending NPAR = 1 because NCORE/NPAR is not compatible with this job type."
        )
        calc.set(npar=1, ncore=None)

    new_parameters = (
        calc.parameters
        if incar_copilot == "aggressive"
        else (
            calc.parameters | user_calc_params
            if incar_copilot == "on"
            else user_calc_params
        )
    )
    if changed_parameters := {
        k: new_parameters[k] for k in set(new_parameters) - set(user_calc_params)
    }:
        LOGGER.info(
            f"The following parameters were changed: {sort_dict(changed_parameters)}"
        )

    return new_parameters


def remove_unused_flags(user_calc_params: dict[str, Any]) -> dict[str, Any]:
    """
    Removes unused flags in the INCAR, like EDIFFG if you are doing NSW = 0.

    Parameters
    ----------
    user_calc_params
        The updated user-provided calculator parameters.

    Returns
    -------
    dict
        The updated user-provided calculator parameters.
    """
    if user_calc_params.get("nsw", 0) == 0:
        # Turn off opt flags if NSW = 0
        opt_flags = ("ediffg", "ibrion", "isif", "potim", "iopt")
        for opt_flag in opt_flags:
            user_calc_params.pop(opt_flag, None)

    if not user_calc_params.get("ldau", False) and not user_calc_params.get("ldau_luj"):
        # Turn off +U flags if +U is not even used
        ldau_flags = (
            "ldau",
            "ldauu",
            "ldauj",
            "ldaul",
            "ldautype",
            "ldauprint",
            "ldau_luj",
        )
        for ldau_flag in ldau_flags:
            user_calc_params.pop(ldau_flag, None)

    # Remove None keys
    none_keys = [k for k, v in user_calc_params.items() if v is None]
    for none_key in none_keys:
        del user_calc_params[none_key]

    return user_calc_params


def normalize_params(user_calc_params: dict[str, Any]) -> dict[str, Any]:
    """
    Normalizes the user-provided calculator parameters.

    Parameters
    ----------
    user_calc_params
        The user-provided calculator parameters.

    Returns
    -------
    dict
        The updated user-provided calculator parameters.
    """
    for k, v in user_calc_params.items():
        if isinstance(v, str):
            user_calc_params[k] = v.lower()
    return user_calc_params


def set_auto_dipole(
    user_calc_params: dict[str, Any], input_atoms: Atoms
) -> dict[str, Any]:
    """
    Sets flags related to the auto_dipole kwarg.

    Parameters
    ----------
    user_calc_params
        The user-provided calculator parameters.
    input_atoms
        The input atoms.

    Returns
    -------
    dict
        The updated user-provided calculator parameters.
    """
    com = input_atoms.get_center_of_mass(scaled=True)
    if "dipol" not in user_calc_params:
        user_calc_params["dipol"] = com
    if "idipol" not in user_calc_params:
        user_calc_params["idipol"] = 3
    if "ldipol" not in user_calc_params:
        user_calc_params["ldipol"] = True

    return user_calc_params


def set_pmg_kpts(
    user_calc_params: PmgKpts,
    pmg_kpts: dict[Literal["line_density", "kppvol", "kppa"], float],
    input_atoms: Atoms,
) -> dict[str, Any]:
    """
    Shortcuts for pymatgen k-point generation schemes.

    Parameters
    ----------
    user_calc_params
        The user-provided calculator parameters.
    pmg_kpts
        The pmg_kpts kwarg.
    input_atoms
        The input atoms.

    Returns
    -------
    dict
        The updated user-provided calculator parameters.
    """
    kpts, gamma = convert_pmg_kpts(
        pmg_kpts, input_atoms, force_gamma=user_calc_params.get("gamma", False)
    )
    reciprocal = bool(pmg_kpts.get("line_density"))

    user_calc_params["kpts"] = kpts
    if reciprocal and user_calc_params.get("reciprocal") is None:
        user_calc_params["reciprocal"] = reciprocal
    if user_calc_params.get("gamma") is None:
        user_calc_params["gamma"] = gamma

    return user_calc_params


class MPtoASEParams:
    """
    Convert an MP-formatted input set to an ASE-formatted input set.
    """

    def __init__(
        self, atoms: Atoms | None = None, prev_dir: SourceDirectory | None = None
    ) -> None:
        """
        Initialize the converter.

        Parameters
        ----------
        atoms
            The ASE atoms object.
        prev_dir
            The previous directory.

        Returns
        -------
        None
        """
        if atoms is None and prev_dir is None:
            raise ValueError("Either atoms or prev_dir must be provided.")
        self.atoms = atoms
        self.prev_dir = prev_dir
        if self.atoms:
            self.ase_sort, self.ase_resort = Vasp_()._make_sort(self.atoms)
            self.structure = AseAtomsAdaptor.get_structure(self.atoms[self.ase_sort])

    def convert_dict_set(self, dict_set: DictSet) -> dict:
        """
        Convert a Pymatgen DictSet to a dictionary of ASE VASP parameters.

        Parameters
        ----------
        dict_set
            The pymatgen DictSet.

        Returns
        -------
        dict
            The ASE VASP parameters.
        """
        input_set = dict_set(sort_structure=False)
        vasp_input = input_set.get_input_set(
            structure=self.structure, potcar_spec=True, prev_dir=self.prev_dir
        )
        self.incar_dict = vasp_input["INCAR"]
        self.pmg_kpts = vasp_input.get("KPOINTS")
        self.potcar_symbols = vasp_input["POTCAR.spec"].split("\n")
        self.potcar_functional = input_set.potcar_functional
        self.poscar = vasp_input["POSCAR"]
        return self._convert()

    @requires(has_atomate2, "atomate2 is not installed.")
    def convert_vasp_maker(self, VaspMaker: BaseVaspMaker) -> dict:
        """
        Convert an atomate2 VaspMaker to a dictionary of ASE VASP parameters.

        Parameters
        ----------
        VaspMaker
            The atomate2 VaspMaker.

        Returns
        -------
        dict
            The ASE VASP parameters.
        """
        input_set_generator = VaspMaker().input_set_generator
        assert hasattr(input_set_generator, "sort_structure")
        input_set_generator.sort_structure = False
        input_set = input_set_generator.get_input_set(
            structure=self.structure, potcar_spec=True, prev_dir=self.prev_dir
        )
        self.incar_dict = input_set.incar
        self.pmg_kpts = input_set.kpoints
        self.potcar_symbols = (
            input_set.potcar.split("\n")
            if isinstance(input_set.potcar, str)
            else input_set.potcar
        )
        self.potcar_functional = input_set_generator.potcar_functional
        self.poscar = input_set.poscar
        return self._convert()

    def _convert(self) -> dict:
        """
        Convert the MP input to a dictionary of ASE VASP parameters.

        Returns
        -------
        dict
            The ASE VASP parameters.
        """
        self.incar_dict = {k.lower(): v for k, v in self.incar_dict.items()}
        pp = self.potcar_functional.split("_")[0]
        potcar_setups = {symbol.split("_")[0]: symbol for symbol in self.potcar_symbols}
        for k, v in potcar_setups.items():
            if k in v:
                potcar_setups[k] = v.split(k)[-1]

        full_input_params = self.incar_dict | {"setups": potcar_setups, "pp": pp}

        if self.pmg_kpts:
            kpts_dict = self.pmg_kpts.as_dict()
            full_input_params |= {
                "kpts": kpts_dict["kpoints"][0],
                "gamma": kpts_dict["generation_style"].lower() == "gamma",
            }

        return full_input_params
