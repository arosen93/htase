from ase.atoms import Atoms
from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.core.surface import generate_all_slabs, Slab
from pymatgen.core import Structure
from pymatgen.analysis.adsorption import AdsorbateSiteFinder
import numpy as np
import warnings

# NOTES:
# - Anytime an Atoms object is converted to a pmg structure, make sure
# to reattach any .info flags to the Atoms object.
# - All major functions should take in Atoms by default and reutrn Atoms
# by default. Pymatgen structures can be returned with an optional kwarg.
# - If you modify the properties of an input Atoms object in any way, make sure to do so
# on a deepcopy because Atoms objects are mutable.


def check_is_metal(atoms):
    """
    Checks if a structure is a likely metal.

    Args:
        atoms (ase.Atoms): ASE atoms object

    Returns:
        is_metal (bool): True if the structure is likely a metal; False otherwise
    """
    if isinstance(atoms, Atoms):
        struct = AseAtomsAdaptor.get_structure(atoms)
    else:
        struct = atoms
    is_metal = all(k.is_metal for k in struct.composition.keys())
    return is_metal


def get_highest_block(atoms):
    """
    Get the highest block (e.g. p-block, d-block f-block) of a structure

    Args:
        atoms (ase.Atoms): ASE atoms object

    Returns:
        highest_block (str): highest block of the structure
    """
    if isinstance(atoms, Atoms):
        struct = AseAtomsAdaptor.get_structure(atoms)
    else:
        struct = atoms
    blocks = [site.specie.block for site in struct]
    if "f" in blocks:
        max_block = "f"
    elif "d" in blocks:
        max_block = "d"
    elif "p" in blocks:
        max_block = "p"
    else:
        max_block = "s"

    return max_block


# internal Pymatgen-only function
def invert_slab(slab_struct, return_struct=False):
    """
    Function to invert a Pymatgen slab object, keeping the vacuum
    space in place.

    Args:
        slab_struct (pymatgen.core.surface.Slab): slab to invert
        return_struct (bool): True if a Pymatgen structure (technically, slab) object
        should be returned; False if an ASE atoms object should be returned
            Defaults to False

    Returns:
        inverted_slab (ase.Atoms or pymatgen.core.surface.Slab): inverted slab
    """
    if not isinstance(slab_struct, Slab):
        raise TypeError("slab must be a pymatgen.core.surface.Slab object")
    frac_coords = slab_struct.frac_coords
    max_z = np.max(frac_coords[:, -1])
    min_z = np.min(frac_coords[:, -1])
    frac_coords[:, -1] = max_z + min_z - frac_coords[:, -1]
    oriented_cell = slab_struct.oriented_unit_cell
    oriented_frac_coords = oriented_cell.frac_coords
    max_oriented_c = np.max(oriented_frac_coords[:, -1])
    min_oriented_c = np.min(oriented_frac_coords[:, -1])
    oriented_frac_coords[:, -1] = (
        max_oriented_c + min_oriented_c - oriented_frac_coords[:, -1]
    )
    inverted_oriented_cell = Structure(
        oriented_cell.lattice,
        oriented_cell.species,
        oriented_frac_coords,
        site_properties=oriented_cell.site_properties,
    )
    inverted_slab_struct = Slab(
        slab_struct.lattice,
        species=slab_struct.species,
        coords=frac_coords,
        miller_index=slab_struct.miller_index,
        oriented_unit_cell=inverted_oriented_cell,
        shift=-slab_struct.shift,
        scale_factor=slab_struct.scale_factor,
        site_properties=slab_struct.site_properties,
    )
    if return_struct:
        inverted_slab = inverted_slab_struct
    else:
        inverted_slab = AseAtomsAdaptor.get_atoms(inverted_slab_struct)

    return inverted_slab


def make_slabs_from_bulk(
    atoms,
    max_index=1,
    min_slab_size=7.0,
    min_length_width=8.0,
    min_vacuum_size=20.0,
    z_fix=2.0,
    flip_asymmetric=True,
    required_surface_atoms=None,
    **slabgen_kwargs,
):
    """
    Function to make slabs from a bulk atoms object.
    The defaults for the size of the slabs are based on those used
    in the Open Catalysis Project (https://doi.org/10.1021/acscatal.0c04525).

    Args:
        atoms (ase.Atoms): bulk atoms
        max_index (int): maximum Miller index for slab generation
            Defaults to 1.
        min_slab_size (float): minimum slab size (depth) in angstroms
            Defaults to 7.0
        min_length_width (float): minimum length and width of the slab in angstroms
            Defaults to 8.0
        min_vacuum_size (float): minimum vacuum size in angstroms
            Defaults to 20.0
        z_fix (float): distance (in angstroms) from top of slab for which atoms should be fixed
            Defaults to 2.0
        flip_asymmetric (bool): If an asymmetric surface should be flipped and added to the list
            Defaults to True.
        required_surface_atoms (list of str): List of chemical symbols that must be present on the
        surface of the slab otherwise the slab will be discarded, e.g. ["Cu", "Ni"]
            Defaults to None.
        **slabgen_kwargs: keyword arguments to pass to the pymatgen generate_all_slabs() function

    Returns:
        final_slabs (ase.Atoms): all generated slabs
    """

    # Note: This will not work as expected if the slab crosses the
    # unit cell boundary or for 2D systems. See Oxana/Martin's code
    # for the 2D workflow: https://github.com/oxana-a/atomate/blob/ads_wf/atomate/vasp/firetasks/adsorption_tasks.py

    # Use pymatgen to generate slabs
    if isinstance(atoms, Atoms):
        struct = AseAtomsAdaptor.get_structure(atoms)
    else:
        struct = atoms

    if isinstance(required_surface_atoms, str):
        required_surface_atoms = [required_surface_atoms]

    # Call generate_all_slabs()
    slabs = [
        slab
        for slab in generate_all_slabs(
            struct, max_index, min_slab_size, min_vacuum_size, **slabgen_kwargs
        )
    ]

    # If the two terminations are not equivalent, make new slab
    # by inverting the original slab and add it to the list
    if flip_asymmetric:
        new_slabs = []
        for slab in slabs:
            if not slab.is_symmetric():
                new_slab = invert_slab(slab, return_struct=True)
                new_slabs.append(new_slab)
        slabs.extend(new_slabs)

    # For each slab, make sure the lengths and widths are large enough
    # and fix atoms z_fix away from the top of the slab.
    final_slabs = []
    for slab in slabs:

        # Supercell creation (if necessary)
        a_factor = int(np.ceil(min_length_width / slab.lattice.abc[0]))
        b_factor = int(np.ceil(min_length_width / slab.lattice.abc[1]))
        final_slab = slab.copy()
        final_slab.make_supercell([a_factor, b_factor, 1])

        # Apply constraints by distance from top surface
        # This does not actually create an adsorbate. It is just a
        # useful function for finding surface vs. subsurface sites
        # since you can't just do z_max - z_fix
        if z_fix:
            final_slab = AdsorbateSiteFinder(
                final_slab, selective_dynamics=True, height=z_fix
            ).slab

            surface_species = [
                site.specie.symbol
                for site in final_slab
                if site.properties["surface_properties"] == "surface"
            ]

            # Check that the desired atoms are on the surface
            if required_surface_atoms and ~np.any(
                [
                    required_surface_atom in surface_species
                    for required_surface_atom in required_surface_atoms
                ]
            ):
                continue

        # Add slab to list
        final_slab = AseAtomsAdaptor.get_atoms(final_slab)
        final_slab.info = atoms.info
        final_slabs.append(final_slab)

    if len(final_slabs) == 0:
        final_slabs = None

    return final_slabs


def make_max_slabs_from_bulk(
    atoms,
    max_slabs,
    max_index=1,
    min_slab_size=7.0,
    min_length_width=8.0,
    min_vacuum_size=20.0,
    z_fix=2.0,
    flip_asymmetric=True,
    required_surface_atoms=None,
    **slabgen_kwargs,
):

    """
    Generate no more than max_slabs number of slabs from a bulk structure.
    The procedure is as follows:
    1. Generate all slabs
    2. If number of slabs is greater than max_slabs, tune ftol from 0.1 to 0.8
    in increments of 0.1.
    3. If number of slabs is still greater than max_slabs, only return the slabs
    with the fewest number of atoms per cell such that the returned amount is
    less than or equal to max_slabs.

    Args:
        atoms (ase.Atoms): bulk structure to generate slabs from
        max_slabs (int): maximum number of slabs to generate
        max_index (int): maximum Miller index for slab generation
            Defaults to 1.
        min_slab_size (float): minimum slab size (depth) in angstroms
            Defaults to 7.0
        min_length_width (float): minimum length and width of the slab in angstroms
            Defaults to 8.0
        min_vacuum_size (float): minimum vacuum size in angstroms
            Defaults to 20.0
        z_fix (float): distance (in angstroms) from top of slab for which atoms should be fixed
            Defaults to 2.0
        flip_asymmetric (bool): If an asymmetric surface should be flipped and added to the list
        required_surface_atoms (list of str): List of chemical symbols that must be present on the
        surface of the slab otherwise the slab will be discarded, e.g. ["Cu", "Ni"]
            Defaults to None.
        **slabgen_kwargs: keyword arguments to pass to the pymatgen generate_all_slabs() function

    Returns:
        slabs (list): list of pymatgen.core.surface.Slab objects

    """

    slabs = make_slabs_from_bulk(
        atoms,
        max_index=max_index,
        min_slab_size=min_slab_size,
        min_length_width=min_length_width,
        min_vacuum_size=min_vacuum_size,
        z_fix=z_fix,
        flip_asymmetric=flip_asymmetric,
        required_surface_atoms=required_surface_atoms,
        **slabgen_kwargs,
    )

    # Try to reduce the number of slabs if the user really wants it...
    # (desperate times call for desperate measures)
    if max_slabs and slabs is not None and len(slabs) > max_slabs:

        if len(slabs) > max_slabs:
            warnings.warn(
                f"You requested {max_slabs} slabs, but {len(slabs)} were generated. Tuning ftol in generate_all_slabs() to try to reduce the number of slabs, at the expense of sampling fewer surface configurations.",
                UserWarning,
            )
            for ftol in np.arange(0.1, 0.9, 0.1):
                slabgen_kwargs["ftol"] = ftol
                slabs_ftol = make_slabs_from_bulk(
                    atoms,
                    max_index=max_index,
                    min_slab_size=min_slab_size,
                    min_length_width=min_length_width,
                    min_vacuum_size=min_vacuum_size,
                    z_fix=z_fix,
                    flip_asymmetric=flip_asymmetric,
                    required_surface_atoms=required_surface_atoms,
                    **slabgen_kwargs,
                )
                if len(slabs_ftol) < len(slabs):
                    slabs = slabs_ftol
                if len(slabs) <= max_slabs:
                    break

        if len(slabs) > max_slabs:
            warnings.warn(
                f"You requested {max_slabs} slabs, but {len(slabs)} were generated. Could not reduce further. Picking the smallest slabs by number of atoms.",
                UserWarning,
            )
            slabs.sort(key=lambda s: len(s))
            if max_slabs == 1:
                slabs = [slabs[0]]
            else:
                slabs = slabs[0:max_slabs]

    return slabs
