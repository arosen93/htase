from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("GITHUB_ACTIONS") and os.name == "nt",
    reason="Skipping this test on Windows in GitHub Actions.",
)  # this works locally on Windows, but no clue why it fails on GitHub Actions

from importlib import util
from pathlib import Path

import numpy as np
from ase.build import bulk, molecule
from monty.shutil import copy_r

from quacc import change_settings
from quacc.recipes.vasp.core import (
    ase_relax_job,
    double_relax_flow,
    freq_job,
    non_scf_job,
    relax_job,
    static_job,
)
from quacc.recipes.vasp.mp import (
    mp_pre_relax_job,
    mp_relax_flow,
    mp_relax_job,
    mp_static_job,
)
from quacc.recipes.vasp.qmof import qmof_relax_job
from quacc.recipes.vasp.slabs import bulk_to_slabs_flow, slab_to_ads_flow
from quacc.recipes.vasp.slabs import relax_job as slab_relax_job
from quacc.recipes.vasp.slabs import static_job as slab_static_job

has_atomate2 = util.find_spec("atomate2") is not None

FILE_DIR = Path(__file__).parent
MOCKED_DIR = FILE_DIR / "mocked_vasp_runs"


def test_static_job(patch_metallic_taskdoc):
    atoms = bulk("Al")

    output = static_job(atoms)
    assert output["nsites"] == len(atoms)
    assert "isym" not in output["parameters"]
    assert output["parameters"]["nsw"] == 0
    assert output["parameters"]["lwave"] is True
    assert output["parameters"]["encut"] == 520
    assert output["parameters"]["efermi"] == "midgap"

    output = static_job(atoms, ncore=2, kpar=4)
    assert output["parameters"]["encut"] == 520
    assert output["parameters"]["ncore"] == 2
    assert output["parameters"]["kpar"] == 4

    output = static_job(atoms, preset="QMOFSet", ismear=0, sigma=0.01, nedos=None)
    assert output["parameters"]["encut"] == 520
    assert output["parameters"]["ismear"] == 0
    assert output["parameters"]["sigma"] == 0.01

    output = static_job(atoms, ivdw=11, lasph=False, prec=None, lwave=None, efermi=None)
    assert output["parameters"]["ivdw"] == 11
    assert output["parameters"]["lasph"] is False
    assert "prec" not in output["parameters"]
    assert "lwave" not in output["parameters"]
    assert "efermi" not in output["parameters"]


def test_relax_job(patch_metallic_taskdoc):
    atoms = bulk("Al")

    output = relax_job(atoms)
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["isym"] == 0
    assert output["parameters"]["nsw"] > 0
    assert output["parameters"]["isif"] == 3
    assert output["parameters"]["lwave"] is False
    assert output["parameters"]["encut"] == 520

    output = relax_job(atoms, nelmin=6)
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["isym"] == 0
    assert output["parameters"]["nsw"] > 0
    assert output["parameters"]["isif"] == 3
    assert output["parameters"]["lwave"] is False
    assert output["parameters"]["encut"] == 520
    assert output["parameters"]["nelmin"] == 6

    output = relax_job(atoms, relax_cell=False)
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["isym"] == 0
    assert output["parameters"]["nsw"] > 0
    assert output["parameters"]["lwave"] is False
    assert output["parameters"]["encut"] == 520
    assert output["parameters"]["isif"] == 2


def test_doublerelax_flow(patch_metallic_taskdoc):
    atoms = bulk("Al")

    output = double_relax_flow(atoms)
    assert output["relax1"]["nsites"] == len(atoms)
    assert output["relax1"]["parameters"]["isym"] == 0
    assert output["relax1"]["parameters"]["nsw"] > 0
    assert output["relax1"]["parameters"]["isif"] == 3
    assert output["relax1"]["parameters"]["lwave"] is False
    assert output["relax1"]["parameters"]["encut"] == 520
    assert output["relax2"]["nsites"] == len(atoms)
    assert output["relax2"]["parameters"]["isym"] == 0
    assert output["relax2"]["parameters"]["nsw"] > 0
    assert output["relax2"]["parameters"]["isif"] == 3
    assert output["relax2"]["parameters"]["lwave"] is False
    assert output["relax2"]["parameters"]["encut"] == 520

    output = double_relax_flow(atoms, relax2_kwargs={"nelmin": 6})
    assert output["relax1"]["nsites"] == len(atoms)
    assert output["relax1"]["parameters"]["isym"] == 0
    assert output["relax1"]["parameters"]["nsw"] > 0
    assert output["relax1"]["parameters"]["isif"] == 3
    assert output["relax1"]["parameters"]["lwave"] is False
    assert output["relax1"]["parameters"]["encut"] == 520
    assert output["relax2"]["nsites"] == len(atoms)
    assert output["relax2"]["parameters"]["isym"] == 0
    assert output["relax2"]["parameters"]["nsw"] > 0
    assert output["relax2"]["parameters"]["isif"] == 3
    assert output["relax2"]["parameters"]["lwave"] is False
    assert output["relax2"]["parameters"]["encut"] == 520
    assert output["relax2"]["parameters"]["nelmin"] == 6

    output = double_relax_flow(atoms, relax_cell=False)
    assert output["relax1"]["nsites"] == len(atoms)
    assert output["relax1"]["parameters"]["isym"] == 0
    assert output["relax1"]["parameters"]["nsw"] > 0
    assert output["relax1"]["parameters"]["lwave"] is False
    assert output["relax1"]["parameters"]["isif"] == 2
    assert output["relax1"]["parameters"]["encut"] == 520
    assert output["relax2"]["nsites"] == len(atoms)
    assert output["relax2"]["parameters"]["isym"] == 0
    assert output["relax2"]["parameters"]["nsw"] > 0
    assert output["relax2"]["parameters"]["lwave"] is False
    assert output["relax2"]["parameters"]["encut"] == 520
    assert output["relax2"]["parameters"]["isif"] == 2

    assert double_relax_flow(atoms, relax1_kwargs={"kpts": [1, 1, 1]})


def test_ase_relax_job(patch_metallic_taskdoc):
    atoms = bulk("Al")

    output = ase_relax_job(atoms)
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["nsw"] == 0
    assert output["parameters"]["lwave"] is False
    assert output["parameters"]["lcharg"] is False
    assert output["parameters"]["encut"] == 520
    assert output["parameters_opt"]["fmax"] == 0.01
    assert len(output["trajectory_results"]) > 1


def test_ase_relax_job2(patch_metallic_taskdoc):
    atoms = bulk("Al")

    output = ase_relax_job(atoms, opt_params={"store_intermediate_results": True})
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["nsw"] == 0
    assert output["parameters"]["lwave"] is False
    assert output["parameters"]["lcharg"] is False
    assert output["parameters"]["encut"] == 520
    assert output["parameters_opt"]["fmax"] == 0.01
    assert len(output["trajectory_results"]) > 1
    assert len(output["steps"]) == len(output["trajectory_results"])


def test_non_scf_job1(patch_metallic_taskdoc):
    atoms = bulk("Al")

    output = non_scf_job(atoms, MOCKED_DIR / "metallic")

    assert "nsites" in output
    assert "parameters" in output
    assert "results" in output

    assert output["parameters"]["lorbit"] == 11
    assert output["parameters"]["lwave"] is False
    assert output["parameters"]["lcharg"] is False
    assert output["parameters"]["nsw"] == 0
    assert output["parameters"]["isym"] == 2
    assert output["parameters"]["icharg"] == 11
    assert output["parameters"].get("kspacing") is None
    assert output["parameters"]["nedos"] == 6001
    assert output["parameters"]["kpts"] == [11, 11, 11]
    assert output["parameters"]["ismear"] == -5
    assert output["parameters"]["nbands"] == 99


def test_non_scf_job2(patch_metallic_taskdoc):
    atoms = bulk("Al")

    output = non_scf_job(
        atoms,
        MOCKED_DIR / "metallic",
        preset="BulkSet",
        nbands_factor=1,
        calculate_optics=True,
    )

    assert "nsites" in output
    assert "parameters" in output
    assert "results" in output

    assert output["parameters"]["loptics"] is True
    assert output["parameters"]["lreal"] is False
    assert output["parameters"]["cshift"] == 1e-5
    assert output["parameters"]["nbands"] == 82
    assert output["parameters"]["ismear"] == -5
    assert output["parameters"]["lorbit"] == 11
    assert output["parameters"]["lwave"] is False
    assert output["parameters"]["lcharg"] is False
    assert output["parameters"]["nsw"] == 0
    assert output["parameters"]["isym"] == 2
    assert output["parameters"]["icharg"] == 11
    assert output["parameters"].get("kspacing") is None


def test_non_scf_job3(patch_metallic_taskdoc):
    atoms = bulk("Al")
    output = non_scf_job(
        atoms, MOCKED_DIR / "metallic", preset="BulkSet", kpts_mode="line"
    )
    assert np.shape(output["parameters"]["kpts"]) == (250, 3)
    assert output["parameters"]["sigma"] == 0.2
    assert output["parameters"]["ismear"] == 1


def test_non_scf_job4(patch_nonmetallic_taskdoc):
    atoms = bulk("Si")
    output = non_scf_job(
        atoms, MOCKED_DIR / "nonmetallic", preset="BulkSet", kpts_mode="line"
    )
    assert np.shape(output["parameters"]["kpts"]) == (193, 3)
    assert output["parameters"]["sigma"] == 0.01
    assert output["parameters"]["ismear"] == 0


def test_non_scf_job5(patch_metallic_taskdoc):
    with pytest.raises(
        ValueError, match="Supported kpoint modes are 'uniform' and 'line' at present"
    ):
        non_scf_job(bulk("Al"), MOCKED_DIR / "metallic", kpts_mode="dummy")


def test_slab_static_job(patch_metallic_taskdoc):
    atoms = bulk("Al")

    output = slab_static_job(atoms)
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["idipol"] == 3
    assert output["parameters"]["nsw"] == 0
    assert output["parameters"]["lvhar"] is True
    assert output["parameters"]["encut"] == 450

    output = slab_static_job(atoms, nelmin=6)
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["idipol"] == 3
    assert output["parameters"]["nsw"] == 0
    assert output["parameters"]["lvhar"] is True
    assert output["parameters"]["encut"] == 450
    assert output["parameters"]["nelmin"] == 6

    output = slab_static_job(atoms, encut=None)
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["idipol"] == 3
    assert output["parameters"]["nsw"] == 0
    assert output["parameters"]["lvhar"] is True
    assert "encut" not in output["parameters"]


def test_slab_relax_job(patch_metallic_taskdoc):
    atoms = bulk("Al")

    output = slab_relax_job(atoms)
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["isif"] == 2
    assert output["parameters"]["nsw"] > 0
    assert output["parameters"]["isym"] == 0
    assert output["parameters"]["lwave"] is False
    assert output["parameters"]["encut"] == 450

    output = slab_relax_job(atoms, nelmin=6)
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["isif"] == 2
    assert output["parameters"]["nsw"] > 0
    assert output["parameters"]["isym"] == 0
    assert output["parameters"]["lwave"] is False
    assert output["parameters"]["encut"] == 450
    assert output["parameters"]["nelmin"] == 6


def test_slab_dynamic_jobs(patch_metallic_taskdoc):
    atoms = bulk("Al")

    ### --------- Test bulk_to_slabs_flow --------- ###

    outputs = bulk_to_slabs_flow(atoms, run_static=False)
    assert len(outputs) == 4
    assert outputs[0]["nsites"] == 45
    assert outputs[1]["nsites"] == 45
    assert outputs[2]["nsites"] == 54
    assert outputs[3]["nsites"] == 42
    assert [output["parameters"]["isif"] == 2 for output in outputs]

    outputs = bulk_to_slabs_flow(atoms)
    assert len(outputs) == 4
    assert outputs[0]["nsites"] == 45
    assert outputs[1]["nsites"] == 45
    assert outputs[2]["nsites"] == 54
    assert outputs[3]["nsites"] == 42
    assert [output["parameters"]["nsw"] == 0 for output in outputs]

    outputs = bulk_to_slabs_flow(
        atoms,
        job_params={"relax_job": {"preset": "SlabSet", "nelmin": 6}},
        run_static=False,
    )
    assert len(outputs) == 4
    assert outputs[0]["nsites"] == 45
    assert outputs[1]["nsites"] == 45
    assert outputs[2]["nsites"] == 54
    assert outputs[3]["nsites"] == 42
    assert [output["parameters"]["isif"] == 2 for output in outputs]
    assert [output["parameters"]["nelmin"] == 6 for output in outputs]
    assert [output["parameters"]["encut"] == 450 for output in outputs]

    outputs = bulk_to_slabs_flow(
        atoms, job_params={"relax_job": {"preset": "SlabSet", "nelmin": 6}}
    )
    assert len(outputs) == 4
    assert outputs[0]["nsites"] == 45
    assert outputs[1]["nsites"] == 45
    assert outputs[2]["nsites"] == 54
    assert outputs[3]["nsites"] == 42
    assert [output["parameters"]["nsw"] == 0 for output in outputs]
    assert [output["parameters"]["nelmin"] == 6 for output in outputs]
    assert [output["parameters"]["encut"] == 450 for output in outputs]

    ### --------- Test slab_to_ads_flow --------- ###
    atoms = outputs[0]["atoms"]
    adsorbate = molecule("H2")

    outputs = slab_to_ads_flow(atoms, adsorbate, run_static=False)

    assert [output["nsites"] == 82 for output in outputs]
    assert [output["parameters"]["isif"] == 2 for output in outputs]

    outputs = slab_to_ads_flow(atoms, adsorbate)
    assert [output["nsites"] == 82 for output in outputs]
    assert [output["parameters"]["nsw"] == 0 for output in outputs]

    outputs = slab_to_ads_flow(
        atoms,
        adsorbate,
        job_params={"relax_job": {"preset": "SlabSet", "nelmin": 6}},
        run_static=False,
    )

    assert [output["nsites"] == 82 for output in outputs]
    assert [output["parameters"]["isif"] == 2 for output in outputs]
    assert [output["parameters"]["nelmin"] == 6 for output in outputs]
    assert [output["parameters"]["encut"] == 450 for output in outputs]

    outputs = slab_to_ads_flow(
        atoms, adsorbate, job_params={"relax_job": {"preset": "SlabSet", "nelmin": 6}}
    )

    assert [output["nsites"] == 82 for output in outputs]
    assert [output["parameters"]["nsw"] == 0 for output in outputs]
    assert [output["parameters"]["nelmin"] == 6 for output in outputs]
    assert [output["parameters"]["encut"] == 450 for output in outputs]

    adsorbate2 = molecule("CH3")
    adsorbate2.set_initial_magnetic_moments([1, 0, 0, 0])
    outputs = slab_to_ads_flow(atoms, adsorbate2)
    assert [output["nsites"] == 84 for output in outputs]
    assert [output["parameters"]["nsw"] == 0 for output in outputs]


def test_qmof(patch_nonmetallic_taskdoc):
    atoms = bulk("Si")
    output = qmof_relax_job(atoms)
    assert output["prerelax_lowacc"]["nsites"] == len(atoms)
    assert output["prerelax_lowacc"]["parameters"]["sigma"] == 0.01
    assert output["prerelax_lowacc"]["parameters"]["isym"] == 0
    assert output["prerelax_lowacc"]["parameters"]["nsw"] == 0
    assert "isif" not in output["prerelax_lowacc"]["parameters"]
    assert "encut" not in output["prerelax_lowacc"]["parameters"]

    assert output["position_relax_lowacc"]["nsites"] == len(atoms)
    assert output["position_relax_lowacc"]["parameters"]["sigma"] == 0.01
    assert output["position_relax_lowacc"]["parameters"]["isym"] == 0
    assert output["position_relax_lowacc"]["parameters"]["nsw"] > 0
    assert output["position_relax_lowacc"]["parameters"]["isif"] == 2
    assert "encut" not in output["prerelax_lowacc"]["parameters"]

    assert output["volume_relax_lowacc"]["nsites"] == len(atoms)
    assert output["volume_relax_lowacc"]["parameters"]["encut"] == 520
    assert output["volume_relax_lowacc"]["parameters"]["sigma"] == 0.01
    assert output["volume_relax_lowacc"]["parameters"]["isym"] == 0
    assert output["volume_relax_lowacc"]["parameters"]["nsw"] > 0
    assert output["volume_relax_lowacc"]["parameters"]["isif"] == 3

    assert output["double_relax"][0]["nsites"] == len(atoms)
    assert output["double_relax"][0]["parameters"]["encut"] == 520
    assert output["double_relax"][0]["parameters"]["sigma"] == 0.01
    assert output["double_relax"][0]["parameters"]["isym"] == 0
    assert output["double_relax"][0]["parameters"]["nsw"] > 0
    assert output["double_relax"][0]["parameters"]["isif"] == 3

    assert output["double_relax"][1]["nsites"] == len(atoms)
    assert output["double_relax"][1]["parameters"]["encut"] == 520
    assert output["double_relax"][1]["parameters"]["isym"] == 0
    assert output["double_relax"][1]["parameters"]["nsw"] > 0
    assert output["double_relax"][1]["parameters"]["isif"] == 3

    assert output["nsites"] == len(atoms)
    assert output["parameters"]["encut"] == 520
    assert output["parameters"]["sigma"] == 0.01
    assert output["parameters"]["isym"] == 0
    assert output["parameters"]["nsw"] == 0
    assert output["parameters"]["laechg"] is True

    output = qmof_relax_job(atoms, run_prerelax=False)
    assert output["prerelax_lowacc"] is None

    output = qmof_relax_job(atoms, nelmin=6)
    assert output["double_relax"][0]["parameters"]["nelmin"] == 6
    assert output["double_relax"][1]["parameters"]["nelmin"] == 6
    assert output["parameters"]["nelmin"] == 6

    output = qmof_relax_job(atoms, relax_cell=False)
    assert "volume-relax" not in output

    assert output["double_relax"][0]["parameters"]["isif"] == 2
    assert output["double_relax"][1]["parameters"]["isif"] == 2


@pytest.mark.skipif(not has_atomate2, reason="atomate2 not installed")
def test_mp_metagga_prerelax_job_metallic(patch_metallic_taskdoc):
    atoms = bulk("Al")
    output = mp_pre_relax_job(atoms, method="metagga", version="legacy")
    assert output["nsites"] == len(atoms)
    assert output["parameters"] == {
        "algo": "all",
        "ediff": 1e-5,
        "ediffg": -0.05,
        "enaug": 1360,
        "encut": 680,
        "gga": "ps",
        "ibrion": 2,
        "isif": 3,
        "ismear": 0,
        "ispin": 2,
        "kspacing": 0.22,
        "laechg": True,
        "lasph": True,
        "lcharg": True,
        "lelf": False,
        "lmixtau": True,
        "lorbit": 11,
        "lreal": "auto",
        "lvtot": True,
        "lwave": True,
        "magmom": [0.6],
        "nelm": 200,
        "nsw": 99,
        "prec": "accurate",
        "setups": {"Al": ""},
        "sigma": 0.05,
        "pp": "pbe",
    }

    output = mp_pre_relax_job(
        atoms, method="metagga", version="legacy", prev_dir=MOCKED_DIR / "metallic"
    )
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["gga"] == "ps"
    assert output["parameters"]["ediffg"] == -0.05
    assert output["parameters"]["encut"] == 680
    assert output["parameters"]["kspacing"] == 0.22
    assert output["parameters"]["ismear"] == 0
    assert output["parameters"]["sigma"] == 0.05
    assert output["parameters"]["pp"] == "pbe"
    assert "metagga" not in output["parameters"]


@pytest.mark.skipif(not has_atomate2, reason="atomate2 not installed")
def test_mp_metagga_prerelax_job_nonmetallic(patch_nonmetallic_taskdoc):
    atoms = bulk("Si")
    output = mp_pre_relax_job(
        atoms, method="metagga", version="legacy", prev_dir=MOCKED_DIR / "nonmetallic"
    )
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["gga"] == "ps"
    assert output["parameters"]["ediffg"] == -0.05
    assert output["parameters"]["encut"] == 680
    assert output["parameters"]["kspacing"] == pytest.approx(0.28752476644932956)
    assert output["parameters"]["ismear"] == 0
    assert output["parameters"]["sigma"] == 0.05
    assert output["parameters"]["pp"] == "pbe"
    assert "metagga" not in output["parameters"]


@pytest.mark.skipif(not has_atomate2, reason="atomate2 not installed")
def test_mp_metagga_relax_job_metallic(patch_metallic_taskdoc):
    atoms = bulk("Al")
    ref_parameters = {
        "algo": "all",
        "ediff": 1e-5,
        "ediffg": -0.02,
        "enaug": 1360,
        "encut": 680,
        "ibrion": 2,
        "isif": 3,
        "ismear": 0,
        "ispin": 2,
        "kspacing": 0.22,
        "laechg": True,
        "lasph": True,
        "lcharg": True,
        "lelf": False,
        "lmixtau": True,
        "lorbit": 11,
        "lreal": "auto",
        "lvtot": True,
        "lwave": True,
        "magmom": [0.6],
        "metagga": "r2scan",
        "nelm": 200,
        "nsw": 99,
        "prec": "accurate",
        "sigma": 0.05,
        "pp": "pbe",
        "setups": {"Al": ""},
    }
    ref_parameters2 = ref_parameters.copy()
    ref_parameters2["magmom"] = [0.0]

    output = mp_relax_job(atoms, method="metagga", version="legacy")
    assert output["parameters"] == ref_parameters
    assert output["nsites"] == len(atoms)

    output = mp_relax_job(
        atoms, method="metagga", version="legacy", prev_dir=MOCKED_DIR / "metallic"
    )
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["metagga"].lower() == "r2scan"
    assert output["parameters"]["ediffg"] == -0.02
    assert output["parameters"]["encut"] == 680
    assert output["parameters"]["kspacing"] == 0.22
    assert output["parameters"]["ismear"] == 0
    assert output["parameters"]["sigma"] == 0.05
    assert output["parameters"]["pp"] == "pbe"


@pytest.mark.skipif(not has_atomate2, reason="atomate2 not installed")
def test_mp_metagga_relax_job_nonmetallic(patch_nonmetallic_taskdoc):
    atoms = bulk("Si")
    output = mp_relax_job(
        atoms, method="metagga", version="legacy", prev_dir=MOCKED_DIR / "nonmetallic"
    )
    assert output["nsites"] == len(atoms)
    assert output["parameters"]["metagga"].lower() == "r2scan"
    assert output["parameters"]["ediffg"] == -0.02
    assert output["parameters"]["encut"] == 680
    assert output["parameters"]["kspacing"] == pytest.approx(0.28752476644932956)
    assert output["parameters"]["ismear"] == 0
    assert output["parameters"]["sigma"] == 0.05
    assert output["parameters"]["pp"] == "pbe"


@pytest.mark.skipif(not has_atomate2, reason="atomate2 not installed")
def test_mp_metagga_static_job(patch_metallic_taskdoc):
    atoms = bulk("Al")

    output = mp_static_job(atoms, method="metagga", version="legacy")
    assert output["nsites"] == len(atoms)
    assert output["parameters"] == {
        "algo": "fast",
        "ediff": 1e-05,
        "enaug": 1360,
        "encut": 680,
        "ismear": -5,
        "ispin": 2,
        "kspacing": 0.22,
        "laechg": True,
        "lasph": True,
        "lcharg": True,
        "lelf": False,
        "lmixtau": True,
        "lorbit": 11,
        "lreal": False,
        "lvtot": True,
        "lwave": False,
        "magmom": [0.6],
        "metagga": "r2scan",
        "nelm": 200,
        "nsw": 0,
        "prec": "accurate",
        "sigma": 0.05,
        "pp": "pbe",
        "setups": {"Al": ""},
    }


@pytest.mark.skipif(not has_atomate2, reason="atomate2 not installed")
def test_mp_metagga_relax_flow_metallic(tmp_path, patch_metallic_taskdoc):
    with change_settings({"CREATE_UNIQUE_DIR": False, "RESULTS_DIR": tmp_path}):
        copy_r(MOCKED_DIR / "metallic", tmp_path)
        atoms = bulk("Al")
        output = mp_relax_flow(atoms, method="metagga", version="legacy")
        assert output["static"]["nsites"] == len(atoms)
        assert output["pre_relax"]["parameters"]["gga"] == "ps"
        assert output["pre_relax"]["parameters"]["ismear"] == 0
        assert output["pre_relax"]["parameters"]["pp"] == "pbe"
        assert output["pre_relax"]["parameters"]["magmom"] == [0.6]
        assert output["relax"]["parameters"]["magmom"] == [0.0]
        assert output["relax"]["parameters"]["metagga"].lower() == "r2scan"
        assert output["relax"]["parameters"]["ediffg"] == -0.02
        assert output["relax"]["parameters"]["encut"] == 680
        assert output["relax"]["parameters"]["ismear"] == 0
        assert output["relax"]["parameters"]["sigma"] == 0.05
        assert output["relax"]["parameters"]["kspacing"] == 0.22
        assert output["relax"]["parameters"]["pp"] == "pbe"


@pytest.mark.skipif(not has_atomate2, reason="atomate2 not installed")
def test_mp_metagga_relax_flow_nonmetallic(tmp_path, patch_nonmetallic_taskdoc):
    with change_settings({"CREATE_UNIQUE_DIR": False, "RESULTS_DIR": tmp_path}):
        copy_r(MOCKED_DIR / "nonmetallic", tmp_path)
        atoms = bulk("Si")
        atoms.set_initial_magnetic_moments([0.0, 0.0])
        output = mp_relax_flow(atoms, method="metagga", version="legacy")
        assert output["pre_relax"]["parameters"]["ismear"] == 0
        assert output["pre_relax"]["parameters"]["pp"] == "pbe"
        assert output["pre_relax"]["parameters"]["magmom"] == [0.0, 0.0]
        assert output["relax"]["parameters"]["magmom"] == [0.0, 0.0]
        assert output["relax"]["parameters"]["metagga"].lower() == "r2scan"
        assert output["relax"]["parameters"]["ediffg"] == -0.02
        assert output["relax"]["parameters"]["encut"] == 680
        assert output["relax"]["parameters"]["ismear"] == 0
        assert output["relax"]["parameters"]["kspacing"] == pytest.approx(
            0.28752476644932956
        )
        assert output["relax"]["parameters"]["pp"] == "pbe"
        assert output["static"]["nsites"] == len(atoms)

        atoms = molecule("O2")
        atoms.set_initial_magnetic_moments([1.0, 0.0])
        atoms.center(vacuum=10)
        atoms.pbc = True
        output = mp_relax_flow(atoms, method="metagga", version="legacy")
        assert output["pre_relax"]["parameters"]["ismear"] == 0
        assert output["pre_relax"]["parameters"]["pp"] == "pbe"
        assert output["pre_relax"]["parameters"]["magmom"] == [1.0, 0.0]
        assert output["relax"]["parameters"]["metagga"].lower() == "r2scan"
        assert output["relax"]["parameters"]["ediffg"] == -0.02
        assert output["relax"]["parameters"]["encut"] == 680
        assert output["relax"]["parameters"]["ismear"] == 0
        assert output["relax"]["parameters"]["kspacing"] == pytest.approx(
            0.28752476644932956
        )
        assert output["relax"]["parameters"]["pp"] == "pbe"
        assert output["relax"]["parameters"]["magmom"] == [0.0, 0.0]
        assert output["static"]["nsites"] == len(atoms)
        assert output["static"]["parameters"]["ismear"] == -5
        assert output["static"]["parameters"]["nsw"] == 0
        assert output["static"]["parameters"]["algo"] == "fast"
        assert output["static"]["parameters"]["magmom"] == [0.0, 0.0]


@pytest.mark.skipif(not has_atomate2, reason="atomate2 not installed")
def test_mp_gga_relax_job(patch_nonmetallic_taskdoc):
    atoms = bulk("Ni") * (2, 1, 1)
    atoms[0].symbol = "O"
    del atoms.arrays["initial_magmoms"]
    output = mp_relax_job(atoms, method="gga", version="legacy")

    assert output["nsites"] == len(atoms)
    assert output["parameters"] == {
        "algo": "fast",
        "ediff": 0.0001,
        "encut": 520,
        "gamma": True,
        "ibrion": 2,
        "isif": 3,
        "ismear": -5,
        "ispin": 2,
        "kpts": (5, 11, 11),
        "lasph": True,
        "ldau": True,
        "ldauj": [0, 0],
        "ldaul": [0, 2],
        "ldauprint": 1,
        "ldautype": 2,
        "ldauu": [0, 6.2],
        "lmaxmix": 4,
        "lorbit": 11,
        "lreal": "auto",
        "lwave": False,
        "magmom": [0.6, 5.0],
        "nelm": 100,
        "nsw": 99,
        "prec": "accurate",
        "sigma": 0.05,
        "pp": "pbe",
        "setups": {"O": "", "Ni": "_pv"},
    }
    assert output["atoms"].get_chemical_symbols() == ["O", "Ni"]


@pytest.mark.skipif(not has_atomate2, reason="atomate2 not installed")
def test_mp_gga_static_job(patch_nonmetallic_taskdoc):
    atoms = bulk("Ni") * (2, 1, 1)
    atoms[0].symbol = "O"
    del atoms.arrays["initial_magmoms"]
    output = mp_static_job(atoms, method="gga", version="legacy")
    assert output["nsites"] == len(atoms)
    assert output["parameters"] == {
        "algo": "fast",
        "ediff": 0.0001,
        "encut": 520,
        "gamma": True,
        "ismear": -5,
        "ispin": 2,
        "kpts": (6, 13, 13),
        "lasph": True,
        "lcharg": True,
        "ldau": True,
        "ldauj": [0, 0],
        "ldaul": [0, 2],
        "ldauprint": 1,
        "ldautype": 2,
        "ldauu": [0, 6.2],
        "lmaxmix": 4,
        "lorbit": 11,
        "lreal": False,
        "lwave": False,
        "magmom": [0.6, 5],
        "nelm": 100,
        "nsw": 0,
        "prec": "accurate",
        "sigma": 0.05,
        "pp": "pbe",
        "setups": {"Ni": "_pv", "O": ""},
    }


@pytest.mark.skipif(not has_atomate2, reason="atomate2 not installed")
def test_mp_gga_relax_flow(tmp_path, patch_nonmetallic_taskdoc):
    with change_settings({"CREATE_UNIQUE_DIR": False, "RESULTS_DIR": tmp_path}):
        copy_r(MOCKED_DIR / "nonmetallic", tmp_path)

        atoms = bulk("Ni") * (2, 1, 1)
        atoms[0].symbol = "O"
        del atoms.arrays["initial_magmoms"]
        output = mp_relax_flow(atoms, method="gga", version="legacy")
        relax_params = {
            "algo": "fast",
            "ediff": 0.0001,
            "encut": 520,
            "gamma": True,
            "ibrion": 2,
            "isif": 3,
            "ismear": -5,
            "ispin": 2,
            "kpts": (5, 11, 11),
            "lasph": True,
            "ldau": True,
            "ldauj": [0, 0],
            "ldaul": [0, 2],
            "ldauprint": 1,
            "ldautype": 2,
            "ldauu": [0, 6.2],
            "lmaxmix": 4,
            "lorbit": 11,
            "lreal": "auto",
            "lwave": False,
            "magmom": [0.6, 5],
            "nelm": 100,
            "nsw": 99,
            "prec": "accurate",
            "sigma": 0.05,
            "pp": "pbe",
            "setups": {"O": "", "Ni": "_pv"},
        }
        relax2_params = relax_params.copy()
        relax2_params["magmom"] = [0.0, 0.0]

        assert output["pre_relax"]["parameters"] == relax_params
        assert output["relax"]["parameters"] == relax2_params
        assert output["static"]["parameters"] == {
            "algo": "fast",
            "ediff": 0.0001,
            "encut": 520,
            "gamma": True,
            "ismear": -5,
            "ispin": 2,
            "kpts": (6, 13, 13),
            "lasph": True,
            "lcharg": True,
            "ldau": True,
            "ldauj": [0, 0],
            "ldaul": [0, 2],
            "ldauprint": 1,
            "ldautype": 2,
            "ldauu": [0, 6.2],
            "lmaxmix": 4,
            "lorbit": 11,
            "lreal": False,
            "lwave": False,
            "magmom": [0.0, 0.0],
            "nelm": 100,
            "nsw": 0,
            "prec": "accurate",
            "sigma": 0.05,
            "pp": "pbe",
            "setups": {"Ni": "_pv", "O": ""},
        }


@pytest.mark.skipif(not has_atomate2, reason="atomate2 not installed")
def test_mp_relax_flow_custom(tmp_path, patch_nonmetallic_taskdoc):
    with change_settings({"CREATE_UNIQUE_DIR": False, "RESULTS_DIR": tmp_path}):
        copy_r(MOCKED_DIR / "nonmetallic", tmp_path)

        atoms = bulk("Ni") * (2, 1, 1)
        atoms[0].symbol = "O"
        del atoms.arrays["initial_magmoms"]
        output = mp_relax_flow(
            mp_relax_flow(
                atoms,
                job_params={
                    "mp_relax_job": {"method": "gga", "version": "legacy", "nsw": 0}
                },
            )["static"]["atoms"],
            job_params={
                "mp_relax_job": {"method": "metagga", "version": "legacy", "nsw": 0}
            },
        )
        assert output["relax"]["parameters"]["nsw"] == 0


def test_freq_job():
    atoms = molecule("H2")
    atoms.pbc = True
    atoms.center(vacuum=1)

    output = freq_job(atoms, kpts=(1, 1, 1))
    assert output["parameters"]["ediff"] == 1e-07
    # Check that "sigma" (only used in ideal_gas) isn't a key in parameters_thermo
    assert "sigma" not in output["parameters_thermo"]
    assert len(output["results"]["vib_freqs_raw"]) == 3 * len(atoms)

    output = freq_job(atoms, kpts=(1, 1, 1), thermo_method="ideal_gas")
    assert output["parameters"]["ediff"] == 1e-07
    assert output["parameters_thermo"]["sigma"] == 2.0
    assert len(output["results"]["vib_freqs_raw"]) == 3 * len(atoms)
    assert len(output["results"]["vib_freqs"]) == 3 * len(atoms) - 5


@pytest.mark.skipif(not has_atomate2, reason="atomate2 not installed")
def test_mp_2024_flow(tmp_path, patch_metallic_taskdoc):
    with change_settings({"CREATE_UNIQUE_DIR": False, "RESULTS_DIR": tmp_path}):
        copy_r(MOCKED_DIR / "metallic", tmp_path)

        atoms = bulk("Al")
        assert mp_relax_flow(atoms, method="gga", version="mp24")
        assert mp_relax_flow(atoms, method="metagga", version="mp24")
