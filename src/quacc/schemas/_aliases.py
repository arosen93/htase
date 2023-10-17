from datetime import datetime
from typing import Any, Literal, TypedDict

from ase import Atoms
from pymatgen.core import Molecule, Structure
from pymatgen.core.composition import Composition
from pymatgen.core.periodic_table import Element


class SymmetryData(TypedDict):
    """
    Type hint associated with `emmet.core.symmetry.SymmetryData`
    """

    crystal_system: str
    symbol: str
    number: int
    point_group: str
    symprec: float
    version: str


class PointGroupData(TypedDict):
    """
    Type hint associated with `emmet.core.symmetry.PointGroupData`
    """

    point_group: str
    rotation_number: float
    linear: bool
    tolerance: float
    eigen_tolerance: float
    matrix_tolerance: float


class EmmetBase(TypedDict):
    """
    Type hint associated with `emmet.core.base.EmmetBaseModel`.
    """

    emmet_version: str
    pymatgen_version: str
    pull_request: int | None
    database_version: str | None
    build_date: datetime
    license: Literal["BY-C", "BY-NC"]


class StructureMetadata(EmmetBase):
    """
    Type hint associated with `emmet.core.structure.StructureMetadata`
    """

    nsites: int
    elements: list[Element]
    nelements: int
    composition: Composition
    formula_pretty: str
    formula_anonymous: str
    chemsys: str
    volume: float
    density: float
    density_atomic: float
    symmetry: SymmetryData


class MoleculeMetadata(EmmetBase):
    """
    Type hint associated with `emmet.core.structure.MoleculeMetadata`
    """

    charge: int
    spin_multiplicity: int
    natoms: int
    elements: list[Element]
    nelements: int
    nelectrons: int
    composition: Composition
    composition_reduced: Composition
    formula_alphabetical: str
    formula_pretty: str
    formula_anonymous: str
    chemsys: str
    symmetry: PointGroupData


class AtomsStructureSchema(StructureMetadata):
    """
    Type hint associated with `quacc.schemas.atoms.atoms_to_metadata`
    for periodic structures.
    """

    atoms: Atoms
    atoms_info: dict[str, Any]  # from atoms.info
    structure: Structure


class AtomsMoleculeSchema(MoleculeMetadata):
    """
    Type hint associated with `quacc.schemas.atoms.atoms_to_metadata`
    for molecules.
    """

    atoms: Atoms
    atoms_info: dict[str, Any]  # from atoms.info
    molecule: Molecule
