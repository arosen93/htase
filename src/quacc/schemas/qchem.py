"""Schemas for Q-Chem"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from maggma.core import Store
from monty.os.path import zpath
from pymatgen.io.qchem.inputs import QCInput
from pymatgen.io.qchem.outputs import QCOutput

from quacc import SETTINGS
from quacc.schemas.ase import summarize_run
from quacc.utils.db import results_to_db
from quacc.utils.dicts import clean_dict

if TYPE_CHECKING:
    from typing import TypedDict

    from ase import Atoms

    from quacc.schemas.ase import RunSchema

    class TaskDoc(TypedDict):
        input: dict  # from QCInput
        output: dict  # from QCOutput

    class QchemSchema(RunSchema):
        taskdoc: TaskDoc


def summarize_qchem_run(
    atoms: Atoms,
    dir_path: str | None = None,
    charge_and_multiplicity: tuple[int, int] | None = None,
    prep_next_run: bool = True,
    remove_empties: bool = False,
    additional_fields: dict | None = None,
    store: Store | None = None,
) -> QchemSchema:
    """
    Get tabulated results from a Q-Chem run and store them in a database-friendly
    format.

    Parameters
    ----------
    atoms
        ASE Atoms object following a calculation.
    dir_path
        Path to VASP outputs. A value of None specifies the current working
        directory
    charge_and_multiplicity
        Charge and spin multiplicity of the Atoms object, only used for Molecule
        metadata.
    prep_next_run
        Whether the Atoms object stored in {"atoms": atoms} should be prepared
        for the next run. This clears out any attached calculator and moves the
        final magmoms to the initial magmoms.
    remove_empties
        Whether to remove None values and empty lists/dicts from the
        TaskDocument.
    additional_fields
        Additional fields to add to the task document.
    store
        Maggma Store object to store the results in. If None,
        `SETTINGS.PRIMARY_STORE` will be used.

    Returns
    -------
    QchemSchema
    """

    additional_fields = additional_fields or {}
    dir_path = dir_path or Path.cwd()
    store = SETTINGS.PRIMARY_STORE if store is None else store

    base_summary = summarize_run(
        atoms,
        charge_and_multiplicity=charge_and_multiplicity,
        prep_next_run=prep_next_run,
        additional_fields=additional_fields,
        store=None,
    )

    taskdoc = {
        "taskdoc": {
            "input": QCInput.from_file(zpath(dir_path / "mol.qin")).as_dict(),
            "output": QCOutput(zpath(dir_path / "mol.qout")).data,
        }
    }

    summary = clean_dict(
        base_summary | taskdoc | additional_fields,
        remove_empties=remove_empties,
    )

    if store:
        results_to_db(store, summary)

    return summary
