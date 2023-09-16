"""Schemas for Q-Chem"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from emmet.core.qchem.task import TaskDocument
from maggma.core import Store

from quacc import SETTINGS
from quacc.schemas.atoms import atoms_to_metadata
from quacc.utils.atoms import prep_next_run as prep_next_run_
from quacc.utils.db import results_to_db
from quacc.utils.dicts import clean_dict

if TYPE_CHECKING:
    from typing import TypeVar

    from ase import Atoms

    QchemSchema = TypeVar("QchemSchema")


def summarize_run(
    atoms: Atoms,
    dir_path: str | None = None,
    prep_next_run: bool = True,
    remove_empties: bool = False,
    additional_fields: dict | None = None,
    store: Store | None = None,
) -> QchemSchema:
    """
    Get tabulated results from a Q-chem run and store them in a database-friendly
    format.

    Parameters
    ----------
    atoms
        ASE Atoms object following a calculation.
    dir_path
        Path to VASP outputs. A value of None specifies the current working
        directory
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
        Dictionary representation of the task document with the following
        fields:

    """

    additional_fields = additional_fields or {}
    run_bader = SETTINGS.VASP_BADER if run_bader is None else run_bader
    dir_path = dir_path or Path.cwd()
    store = SETTINGS.PRIMARY_STORE if store is None else store

    # Fetch all tabulated results from VASP outputs files Fortunately, emmet
    # already has a handy function for this
    results = TaskDocument.from_directory(dir_path).dict()
    uri = results["dir_name"]
    results["nid"] = uri.split(":")[0]
    results["dir_name"] = ":".join(uri.split(":")[1:])
    results["builder_meta"]["build_date"] = str(results["builder_meta"]["build_date"])

    # Remove unnecessary fields
    for k in [
        "calcs_reversed",
        "last_updated",
        "molecule",  # already in output
        "tags",
    ]:
        results.pop(k, None)

    # Prepares the Atoms object for the next run by moving the final magmoms to
    # initial, clearing the calculator state, and assigning the resulting Atoms
    # object a unique ID.
    if prep_next_run:
        atoms = prep_next_run_(atoms)

    # We use get_metadata=False and store_pmg=False because the TaskDocument
    # already makes the molecule metadata for us
    atoms_db = atoms_to_metadata(atoms, get_metadata=False, store_pmg=False)

    # Make task document
    task_doc = clean_dict(
        results | atoms_db | additional_fields, remove_empties=remove_empties
    )

    # Store the results
    if store:
        results_to_db(store, task_doc)

    return task_doc
