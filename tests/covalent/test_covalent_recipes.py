import pytest
from functools import partial

from ase.build import bulk

from quacc import SETTINGS

ct = pytest.importorskip("covalent")
pytestmark = pytest.mark.skipif(
    SETTINGS.WORKFLOW_ENGINE != "covalent",
    reason="This test requires the Covalent workflow engine",
)

from quacc.recipes.emt.core import relax_job
from quacc.recipes.emt.slabs import bulk_to_slabs_flow

def test_covalent_functools(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    atoms = bulk("Cu")
    dispatch_id = ct.dispatch(bulk_to_slabs_flow)(atoms, slab_relax_job=partial(relax_job, opt_params={"fmax": 0.1}))
    output = ct.get_result(dispatch_id, wait=True)
    assert output.status == "COMPLETED"
    assert len(output.result) == 4
    assert "atoms" in output.result[-1]

def test_phonon_flow(tmp_path, monkeypatch):
    pytest.importorskip("phonopy")
    from quacc.recipes.emt.phonons import phonon_flow

    monkeypatch.chdir(tmp_path)
    atoms = bulk("Cu")
    dispatch_id = ct.dispatch(phonon_flow)(atoms)
    output = ct.get_result(dispatch_id, wait=True)
    assert output.status == "COMPLETED"
    assert output.result["results"]["thermal_properties"]["temperatures"].shape == (
        101,
    )


def test_phonon_flow_multistep(tmp_path, monkeypatch):
    pytest.importorskip("phonopy")
    from quacc.recipes.emt.phonons import phonon_flow

    monkeypatch.chdir(tmp_path)
    atoms = bulk("Cu")
    relaxed = relax_job(atoms)
    dispatch_id = ct.dispatch(phonon_flow)(relaxed["atoms"])
    output = ct.get_result(dispatch_id, wait=True)
    assert output.status == "COMPLETED"
    assert output.result["results"]["thermal_properties"]["temperatures"].shape == (
        101,
    )
