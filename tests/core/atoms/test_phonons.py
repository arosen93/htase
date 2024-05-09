from __future__ import annotations

import pytest

pytest.importorskip("phonopy")
pytest.importorskip("seekpath")

import numpy as np
from ase.build import bulk
from numpy.testing import assert_almost_equal, assert_array_equal

from quacc.atoms.phonons import get_phonopy


def test_get_phonopy():
    atoms = bulk("Cu")
    phonopy, should_be_done = get_phonopy(atoms)
    assert_array_equal(phonopy.supercell_matrix, [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    assert should_be_done is None

    phonopy, _ = get_phonopy(atoms, min_lengths=5)
    assert_array_equal(phonopy.supercell_matrix, [[2, 0, 0], [0, 2, 0], [0, 0, 2]])

    phonopy, _ = get_phonopy(atoms, min_lengths=[5, 10, 5])
    assert_array_equal(phonopy.supercell_matrix, [[2, 0, 0], [0, 4, 0], [0, 0, 2]])

    phonopy, _ = get_phonopy(atoms, displacement=1)
    assert_almost_equal(
        phonopy.displacements, [[0, 0.0, np.sqrt(2) / 2, np.sqrt(2) / 2]]
    )

    phonopy, _ = get_phonopy(atoms, symprec=1e-8)
    assert phonopy.symmetry.tolerance == 1e-8

    unfixed_phonopy, fixed_phonopy = get_phonopy(
        atoms, min_lengths=5, fixed_indices=[0, 1]
    )
    assert len(unfixed_phonopy) == 2
    assert len(fixed_phonopy) == 2
