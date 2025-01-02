# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project generally adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.11.10]

## [0.11.9]

### Changed

- ASE>=3.24.0 is required due to upstream breaking changes

### Fixed

- Fixed a bug where DFT+U parameters might not be set appropriately if the `Atoms` object is sorted when using MP input sets

## [0.11.8]

### Added

- Support for SevenNet and Orb models as MLPs

## [0.11.7]

### Added

- New phonopy routines to handle fixed atoms

## [0.11.6]

### Fixed

- Fixed handling of async prefect tasks

## [0.11.5]

### Added

- Added support for atomate2>=0.0.15

### Changed

- Overhauled handling of Prefect futures/states. Refer to the documentation for more details.
- The minimum supported Python version is now 3.10 in alignment with Pymatgen

## [0.11.4]

### Changed

- Put a `<=` version pin on Atomate2 to resolve upstream breaking change

## [0.11.3]

### Added

- Added support for `preset: Path` type in the `Espresso` calculator
- Raise a custom `JobFailure` error when a calculation fails, which stores the directory where the files remain as well as the parent error

### Fixed

- Fixed Parsl MPI support for Espresso recipes
- Fixed miscellaneous inconsistencies with `preset` handling

## [0.11.2]

### Added

- Added support for `preset: Path` type in the `Vasp` calculator

## [0.11.1]

### Added

- Added an `additional_fields` keyword argument to all recipes

### Changed

- Gaussian and ORCA schemas have been updated to reflect the removal of cclib

### Fixed

- Fixed support for Prefect 3
- Fixed support for ORCA 6.0.0

### Removed

- Removed cclib-based schemas due to fragility and replaced them with the standard ASE schemas

## [0.11.0]

### Added

- Added support for HarmonicThermo as a thermochemistry method
- Added a VASP frequency recipe

### Changed

- Overhauled schemas throughout quacc to improve maintainability. They are now classes (mostly) instead of functions.
- Changed the thermo runner to a schema
- Renamed the Q-Chem perturb IRC job to `quasi_irc_job` for internal consistency
- Removed the preliminary relaxation steps from all phonon workflows for greater composability

### Fixed

- Fixed a crash when Espresso checked kpts and kspacing usage

### Removed

- Removed the Q-Chem quasi-IRC job since it was redundant with the perturb IRC job

## [0.10.1]

### Changed

- Overhauled type hinting system
- Added kspacing default to Espresso non_scf_job

### Fixed

- Fixed breaking change from monty 07.12.2024
- Fixed a variety of incompatible type hints

## [0.10.0]

### Added

- Added a function `from quacc import get_settings` to fetch the current settings on a thread
- Added a mechanism to update the settings on-the-fly via a special `settings_swap` keyword argument that can be passed to the decorators when a workflow engine is used.
- Support for MD workflows

### Fixed

- Fixed an edge-case that can occur in multithreading environments where in-memory changes to the `QuaccSettings` could carry over to a concurrent thread
- Made the detection of intermediate step directories more robust

### Removed

- The global `SETTINGS` variable is gone! Modifying a global variable can cause havoc in multithreaded environments and was never compatible with workflow engines. Refer to the [Modifying Settings](https://quantum-accelerators.github.io/quacc/user/settings/settings.html) page for the recommended approach. For most users without an active workflow engine, this will be the `with change_settings()` context manager.

## [0.9.5]

### Changed

- Pinned numpy version to < 2.0 (for now...)

## [0.9.4]

### Added

- VASP: Added a new logging statement to specifically highlight which parameters were swapped, not just which recommendations were made

### Changed

- VASP: Removed EFERMI="midgap" co-pilot swap since it does not influence the results and prevents VASP 5.x compatability

### Fixed

- Fixed MD5-based `Atoms` hashing to work on FIPS-encrypted OSs

## [0.9.3]

### Changed

- Update the default `shear_strain` value in `quacc.atoms.defects.make_deformations_from_bulk` to match that of Pymatgen
- Internal refactoring of the runners to be class-based

### Fixed

- Fixed an issue where the `Atoms` object in the output schema could get a stray calculator attached to it when passed between `@job`s

## [0.9.2]

### Added

- Added support for controlling which properties to calculate with MLP static jobs

### Changed

- Bumped minimum version of pymatgen

## [0.9.1]

### Changed

- No longer need to install `master` branch of ASE
- Modified Espresso and ONETEP settings to support new ASE profile features
- Removed `nsteps` from the `OptSchema`

## [0.9.0]

### Added

- The `RESULTS_DIR` and `SCRATCH_DIR` settings can now be relative paths, if desired

### Changed

- Failed calculations are now stored in a `failed-quacc-12345-` directory to distinguish these tasks from the running tasks in `tmp-quacc-12345-`
- The output schema is now written to a serialized JSON file instead of pickle for security and ease-of-use reasons. It can be rehydrated via `loadfn("quacc_results.json.gz")` where `loadfn` is from `monty.serialization import loadfn`
- The `fmax` attribute was moved from the base level to the `parameters_opt` section since it is an input parameter

### Fixed

- File shuttling after a completed calculation is now faster since we simply rename the directory instead of moving each individual file

## [0.8.0]

### Added

- Added a context handler, `quacc.settings.change_settings`, that can be used to modify global settings temporarily
- Added `quacc.calculators.vasp.params.MPtoASEParams` to convert between Pymatgen- and Atomate2-style input parameters to ASE-compatabile parameters

### Fixed

- Fixed copying of WAVECAR between steps of the QMOF recipes

### Changed

- Overhauled the MP recipes to ensure better compatability with atomate2 workflows
- The workflow engine must be directly specified with `WORKFLOW_ENGINE`, as noted in the docs
- Changed `VASP_MAG_CUTOFF` from 0.05 to 0.02
- Removed the `preset` keyword argument from the QMOF recipes

### Removed

- Removed the `pmg_input_set` keyword argument from the `Vasp` calculator

## [0.7.8]

### Added

- Added support for Parsl "special" keyword arguments (e.g. `timeout`, `parsl_resource_specification`)

### Fixed

- Fixed bug where the common phonon subflow would generate a `Phonopy` object based on the unrelaxed, rather than relaxed, structure
- Sped up the common phonon subflow by removing duplicate `get_phonopy()` calls

## [0.7.7]

### Added

- Added quasi IRC recipes to ORCA and Q-Chem
- Added frequency recipe to ORCA

### Fixed

- Fixed various type hints
- Improved performance for the common phonon flow
- Improved performance for ideal gas thermo calculations

## [0.7.6]

### Fixed

- Fixed file extension for the optimizer trajectories, which should have been `.json` instead of `.pckl`

## [0.7.5]

### Changed

- Removed the `atoms_info` field from the `AtomsSchema` since this is already available in the database via Pymatgen's `MSONAtoms` serialization

## [0.7.4]

### Changed

- Only call `jsanitize` once before uploading to the `Store`

## [0.7.3]

### Added

- Added new Espresso recipes to perform electron-phonon calculations and Fourier interpolation of the phonon potential

### Fixed

- Fixed potential issues with I/O settings and Espresso
- Fixed passing of custom decorators in the Espresso `grid_phonon_flow`

## [0.7.2]

### Changed

- Calculator executable commands are now `str` type instead of `Path`
- Removed `slowconv` from the default parameters of the ORCA recipes
- The Q-Chem calculator now uses the TaskDoc from emmet in its `results` attribute

### Fixed

- Fixed user setting of LOGGER level
- Fixed a glob-based issue with `copy_decompress_files`

## [0.7.1]

### Added

- Added an optional MP compatability checker for MP recipes
- Summaries for intermediate ASE optimization steps are now stored in the output schema for VASP and cclib-based recipes when `store_intermediate_results=True`
- Added a `WRITE_PICKLE` setting, which by default, will write out a `.pkl` file containing the result schema to the directory

### Changed

- Updated `ruff` settings
- The Gaussian and ORCA `static_job` routines do a force calculation by default now

### Fixed

- Fixed input file formatting for `orcablocks` in ORCA recipes

### Removed

- Removed the `CHDIR` setting

## [0.7.0]

### Added

- Added a `non_scf_job` for VASP

### Changed

- There are no more `os.chdir` calls to ensure thread safety
- Use `pymatgen.io.ase.MSONAtoms` to make MSONable `Atoms`
- Changed default NEDOS value from 5001 to 3001 for VASP static jobs (10x the default)

### Fixed

- Fixed multithreaded `@task` distribution with VASP and Q-Chem
- Fixed a bug where, with Prefect, the `State` would raise an indexing error when passing around deferred `dict` entries
- Fixed a bug when `job_parameters` and `job_decorators` are both passed to `customize_funcs()`
- Raise a `ValueError` when the user provides `SCRATCH_DIR` or `RESULTS_DIR` as a relative path

## [0.6.10]

### Fixed

- Fixed pickle-ability of the schemas
- Fixed multithreaded `@task` distribution with GULP, Espresso, and common phonon flow recipes
- Fixed concurrency issues with VASP/Q-Chem due to refactoring

### Removed

- Removed the `quacc.schemas.atoms._quacc_sanitize` function

## [0.6.9]

### Added

- Added MP compatability corrections in VASP MP recipes
- Added various phonon recipes for Espresso
- Added various DOS recipes for Espresso

### Fixed

- Fixed a rare edge case where final magmoms would not be moved to initial magmoms of next run in MP VASP recipes

## [0.6.8]

### Added

- Added an option to prevent `os.chdir` calls for multithread safety
- Added a common elastic calculation

### Changed

- Switched to `ruff` for formatting, replacing the need for `black` and `isort`
- Changed VASP double relaxes to be flows and not jobs
- Changed the behavior of `quacc.utils.files.copy_decompress_files`

### Fixed

- Fixed `copy_files` handling with workflow engines
- Fixed MP VASP double relaxes, where the same relaxation was done twice by mistake
- Fixed use of `**calc_kwargs` in MP flow recipes

## [0.6.7]

### Added

- Added a `store_intermediate_results` keyword option to `quacc.runners.ase.run_opt()` to allow for storing of the logfiles in intermediate geometry optimization steps.
- Added support for Pymatgen-based input sets in VASP jobs
- Added an MP meta-GGA VASP static job
- Added MP GGA relax job, MP GGA static job, and MP GGA relax flow
- Added a validity checker on CLI parameters

### Changed

- Changed the default ASE optimizer from `FIRE` to `BFGS` for most recipes
- Changed the VASP `DoubleRelaxSchema` to be consistent between flows
- Refactored VASP and Q-Chem execution commands in custom calculators

### Fixed

- Fixed `dir_name` in VASP output schema
- Fixed auto-detection of the Prefect workflow engine in settings
- Fixed compatability of MP meta-GGA workflow with that in atomate2

## [0.6.6]

### Fixed

- Using environment variables to set a setting to `None` now works as expected
- Overall, more intuitive and robust handling of settings across the various input methods

## [0.6.5]

### Added

- PDOS jobs and flows for Espresso

### Changed

- Modified the Espresso results schema to be DB-compatible
- The `PRIMARY_STORE` setting has changed to `STORE` and is now formatted more intuitively
- Uses 2024 stable release of `black`

### Fixed

- Fixed usage of `MontyStore` as the data store option

### Removed

- Removed the deprecated "q-chem legacy" recipes

## [0.6.4]

### Added

- Added a `supercell_matrix` keyword argument to the phonon recipes.
- More data is now generated, parsed, and stored in phonon workflows, including total DOS and the automatically generated band structure

### Changed

- The `seekpath` dependency is now required for phonon workflows, as reflected in the `quacc[phonons]` optional dependencies
- Changed the `min_length: float | None` keyword argument in phonon flows to `min_lengths: float | tuple[float, float, float] | None` for greater flexibility. The default value is now set to 20.0 instead of 15.0 as well.

### Fixed

- Fixed occasional edge cases where the charge/spin multiplicity checker would raise a `ValueError` in generating the `RunSchema`
- Fixed phonon flow with MACE-MP-0 when `dispersion=True`

## [0.6.3]

### Added

- Added phonon job for MLPs
- Added an ASE relax job recipe for ONETEP
- Added a non-SCF job for Quantum Espresso
- Added a DOS job for Quantum Espresso
- Added a DOS flow for Quantum Espresso

### Changed

- Redesigned the `common_phonon_flow` to accept new keyword arguments that enable symmetry reduction. A pre-relaxation step is now also carried out by default.

### Fixed

- Ensures the "restart" keyword argument is not set when a SciPy optimizer is used
- Fixed the `ONETEP_CMD` setting to be `str` instead of `Path` when used to instantiate the calculator
- Quantum Espresso restarts are now disabled between steps in ASE relaxations
- Various bug fixes for the Espresso `grid_phonon_flow`
- Fixed redundant `Structure` info in the `RunSchema`

## [0.6.2]

### Changed

- The `CREATE_UNIQUE_DIR` setting is now set to `True` by default.
- The temporary directory name and its symlink have been slightly updated to have "tmp-" and "symlink-" at the front of the name instead of the end for easier file navigation.
- Updated the "trajectory" entry in the `OptSchema` to be `list[Atoms]` instead of `list[AtomsSchema]`

### Fixed

- Fixed an occasional race condition that occurs when running concurrent calculations in multi-threaded mode
- The temporary directory made when a `@job` runs now has a name consistent with the folder where the results will ultimately be stored.
- Significant speedup in generating the `OptSchema`

## [0.6.1]

### Added

- Support for ONETEP recipes (@nekkrad)
- New Espresso recipe for ASE external relaxations (@tomdemeyere)

### Fixed

- Fixed bug where autoamtic k-point schemes in VASP would return `kpts` as `list[float]` instead of `list[int]`
- VASP runs now respect the `CHECK_CONVERGENCE` global setting when set to `False`
- Fixed bug where the gamma-point only version of VASP was being called if `kpts` was `None` but `kspacing` was not `None`

### Removed

- Removed the broken TRICs support with Sella
- Removed the `covalent_to_db` function

## [0.6.0]

### Added

- A new `grid_phonon` recipe in Espresso (@tomdemeyere)
- Preliminary support for the Prefect workflow engine, again, but this time without it breaking everything

### Changed

- Raised the default LOGGER level from `WARNING` to `INFO`

### Fixed

- Codes calling Custodian can be used in Jupyter Notebooks
- Fixed an error in the Espresso `phonon_flow` when using the `master` branch of ASE
- Fixed a few erroneous type hints
- Fixed the `typer` depenendecy in `pyproject.toml` to be `typer[all]` like it was supposed to be
- Fixed a bug when passing decorator keyword arguments when using Dask

## [0.5.2]

### Changed

- ORCA and GULP recipes now use a more intuitive and concise `list[str]` input argument format instead of a `dict` format when overriding defaults

### Fixed

- Fixed concurrency issues with Dask subflows

## [0.5.1]

### Added

- Adds a new `ase_relax_job` for ORCA
- Adds a new `relax_job` and `post_processing_job` for Quantum Espresso
- `quacc.wflow_tools.customizers.strip_decorator` and `quacc.wflow_tools.customizers.redecorate` are imported in the base `__init__.py` for easy user access
- The CLI now has _color_

### Changed

- The test suite's SCRATCH_DIR and RESULTS_DIR are now fixed to a given location
- The default Espresso preset has been changed to "sssp_1.3.0_pbe_efficiency"
- To remove calculator defaults entirely, `quacc.Remove` is recommended in place of `None`
- The `quacc.wflow_tools.customizers.strip_decorator` function is recommended instead of calling `.__wrapped__`

### Fixed

- Fixed Dask subflows that were calling `.compute()`
- Fixed various bugs in the Espresso calculator and recipes

## [0.5.0]

### Added

- Created a `quacc.wflow_tools.customizers` module to aid in customizing pre-made recipes.

### Changed

- Overhauled how sub-jobs in recipes can be dynamically modified by the user to increase flexibility.
- Changed default `fmax` for `quacc.recipes.mlp.core.relax_job` to 0.05.
- Renamed the `quacc.utils.dicts.merge_dicts` function to `._recursive_dict_pair_merge` to better reflect its functionality.
- Renamed the `quacc.utils.dicts.merge_several_dicts` function to `.recursive_dict_merge` to better reflect its functionality.

### Fixed

- Increased support of `~/` throughout quacc file handling mechanisms
- Fixed an infinite recursion error when `copy_decompress_files_from_dir` was run in the current working directory.

## [0.4.6]

### Added

- The `WORKFLOW_ENGINE` quacc setting now accepts `None`.
- A `DEBUG` quacc setting as been added.

### Changed

- The way to run complex, dynamic flows has been modified to rely on `functools.partial()` instead of kwargs. See the updated documentation.
- Refactored test suite

## [0.4.5]

### Added

- Added ML interatomic potential recipes

### Changed

- ASE optimization log files and pickle files are written to disk by default
- Deprecated the old Q-Chem recipes and replaced them with the updated versions

### Removed

- Officially drop support of the Prefect workflow engine

## [0.4.4]

### Added

- Added core Quantum ESPRESSO recipes and custom calculator. (@tomdemeyere)
- Added a new function, `quacc.utils.files.copy_decompress_files_from_dir`

### Changed

- The `copy_files` kwarg in most recipes can now include a directory
- Renamed `quacc.utils.files.copy_decompress` to `quacc.utils.files.copy_decompress_files`

### Fixed

- Quacc settings that are paths now have `~/` expanded in most cases

## [0.4.3]

### Added

- Added preliminary support for the `Dask` workflow engine via Dask Delayed and Dask Distributed.

### Changed

- Renamed `CREATE_UNIQUE_WORKDIR` to `CREATE_UNIQUE_DIR` to better reflect its utility.
- The default for the `SCRATCH_DIR` setting is now `None` instead of `~/.quacc_scratch`. In other words, the default is to not use a scratch directory. This should help with onboarding, and the ability to set it as `None` may be broadly of interest. Setting the `SCRATCH_DIR` to a given `Path` will still work as expected.
- Files are no longer recursively _copied_ from `SCRATCH_DIR` to `RESULTS_DIR`. Instead, they are recursively moved. This should speed up I/O operations.

### Fixed

- Fixed a missing `phonopy_kwargs` keyword argument in `quacc.recipes.common.phonons`

## [0.4.2]

### Added

- Added a Jenkins-based test suite that runs tests on HPC resources without mocking for Gaussian, GULP, ORCA, and VASP (minimal)
- Added a TBLite phonon recipe

### Changed

- Changed the `auto_kpts` kwarg in the `Vasp` calculator to `pmg_kpts`
- Internal refactoring of recipes to have a separate `_base.py` module when appropriate
- Removed the unnecessary `Atoms` arg from the `calc_setup` function

### Fixed

- Fixed slow initial import (3 s --> 1 s)
- Fixed a few broken type hints
- Fixed functional and basis set strings in Gaussian recipes
- Uses number of physical cores instead of logical cores as default for molecular DFT recipes

## [0.4.1]

### Changed

- Switched to using the PyPI release of NewtonNet (1.1).
- NewtonNet recipes don't run a Hessian calculation by default unless needed

### Fixed

- Fixed circular import issue when running Q-Chem calculations.

### Removed

- Removed unsupported `qchem_internal_relax_job`

## [0.4.0]

### Added

- Added `quacc.recipes.common`, including `quacc.recipes.common.slabs`, `quacc.recipes.common.defects`, and `quacc.recipes.common.phonons`
- Added phonopy schema in `quacc.schemas.phonons`
- Added EMT phonon workflow

### Changed

- The method for specifying swaps to the default calculator arguments in recipes has been overhauled. In place of the previous `calc_swaps: dict` approach, additional parameters can be specified via the `**kwargs`. In practice, this means in recipes you can do `scf = "diis", max_steps=100` instead of `calc_swaps={"scf":"diis", "max_steps":100}`, for instance.
- Moved `quacc.runners.calc` to `quacc.runners.ase`
- Moved `quacc.runners.prep` to `quacc.schemas.prep`
- Reduced code duplication across complex flows

## [0.3.13]

### Fixed

- Fixed support for the most recent version of ASE as of 11/2/2023

## [0.3.12]

### Added

- Added more type hints for input keyword arguments
- Added the `quacc info` command-line argument for error reporting

### Changed

- Consolidated VASP INCAR co-pilot settings
- Internal refactoring of the Q-Chem and VASP calculators

### Fixed

- All `Path`-based settings have `.expanduser()` applied

## [0.3.11]

### Changed

- Improved error handling

## [0.3.10]

### Changed

- DFTB+ `MaxSccIterations` set to 200 by default
- SCC errors in DFTB+ relaxations will be reported with higher priority than a relaxation error

## [0.3.9]

### Changed

- Changed prefix of scratch directories to have the datetime in it for easier debugging

### Fixed

- DFTB+ recipes now won't crash when `kpts=None` for structures with PBCs

## [0.3.8]

### Changed

- Changed minimum version of Parsl

## [0.3.7]

### Added

- Added type-hinting for schemas

### Changed

- Recipes now take `Atoms` instead of `Atoms | dict` as input
- Recipes no longer require the use of `fetch_atoms`
- Standardized schema fields

### Removed

- Removed the `fetch_atoms` function

## [0.3.6]

### Fixed

- Fixed VASP recipes to always respect `calc_swaps`.
- Fixed setting multiple cores in Custodian for Q-Chem runs.

## [0.3.5]

### Added

- Added a new `VibThermoSchema` that merges the `VibSchema` and `ThermoSchema` as a convenience

### Changed

- The output of recies no longer automatically removes blank lists/dicts/sets to maintain a consistent schema.
- The tblite `freq_job` and lj `freq_job` now use `VibThermoSchema` as the output
- Changed default `SCRATCH_DIR` from `Path.cwd() / ".scratch"` to `Path("~/.scratch")`

## [0.3.4]

### Added

- Added a new documentation section for worked examples on HPC.

### Changed

- Updated the minimum required versions for Pymatgen and emmet-core to reflect Pydantic 2 update.
- Added `symprec=1e-8` to the default parameters of VASP relaxation jobs.
- VASP bulk recipes now use "BulkSet" as the default preset instead of `None`.
- VASP slab recipes now use "SlabSet" as the default preset instead of `None`.

## [0.3.3]

### Fixed

- Fixed pip version conflict when installing Covalent dependencies.

## [0.3.2]

### Changed

- Migration to Pydantic 2 is complete, along with the corresponding dependencies.

## [0.3.1]

### Changed

- Pydantic field type validation has been improved.
- Moved `quacc.utils.atoms`/`.slabs`/`.defects` into `quacc.atoms.core`/`.slabs`/`.defects`
- Moved `quacc.custodian` to `quacc.calculators.custodian`
- Moved `quacc.utils.thermo.ideal_gas` to `quacc.builders.thermo.run_ideal_gas`
- Renamed `quacc.schemas.ase.summarize_thermo` to `quacc.schemas.ase.summarize_ideal_gas_thermo`

## [0.3.0]

### Changed

- Changed default `SCRATCH_DIR` from `/tmp` to `Path.cwd() / .scratch`
- Refactored decorator handling to be more concise
- Renamed `[optimizers]` extras to `[sella]`
- Moved `quacc.utils.wflows` into `quacc.wflow_tools.decorators` and `quacc.wflow_tools.prefect`
- Moved `quacc.utils.db` into `quacc.wflow_tools.db`
- Moved `quacc.utils.calc` to `quacc.runners.ase`
- Moved `quacc.presets` to `quacc.calculators.presets`

### Fixed

- Fixed parsing of `RESULTS_DIR` and `SCRATCH_DIR` paths when they contain `~`
- Symlinks are no longer created if `RESULTS_DIR == SCRATCH_DIR` since this is redundant
- If `RESULTS_DIR` or `SCRATCH_DIR` are not present, they will be automatically made

## [0.2.8]

### Changed

- Decorators are now applied at import time rather than at function-call time.

### Fixed

- Fixed compatibility with FireWorks.
- Fixed I/O issue on Windows and NFS file systems where Sella optimizations would crash.

## [0.2.7]

### Added

- Added a `freq_job` recipe in Q-Chem (@samblau)
- Added support for TRICs in Sella calculations (@samblau)

### Changed

- Refactored all recipes to prevent code duplication
- Set `LREAL = False` in VASP `BulkSet.yaml`

## [0.2.6]

### Added

- Add support for `Path` objects everywhere possible.

### Changed

- Charge and spin multiplicity are now required arguments in molecular DFT calculators.
- Slab recipes now use `make_slabs_from_bulk` instead of `make_max_slabs_from_bulk`
- Use the `logging` module when warnings do not need to be immediately addressed.
- Functions are no longer used as kwargs in recipes to help with (de)serialization in certain workflow engines.

### Removed

- Removed `make_max_slabs_from_bulk` function.

## [0.2.5]

### Added

- Added support for the Redun workflow engine.
- Added a simple CLI for (un)setting YAML config parameters.

### Changed

- Internal refactoring of the `Vasp` calculator.

### Removed

- Removed the demonstration Jobflow EMT slab recipe.

## [0.2.4]

### Changed

- Updated VASP co-pilot rules and `BulkSet.yaml` in accordance with recent MP benchmarking (#849).
- Moved `fetch_atoms` to `quacc.schemas`.

### Fixed

- VASP: Fixed a scenario where SIGMA was set to 0.05 if the user provided SIGMA > 0.05. This was supposed to happen when ISMEAR = 0 but was previously done when ISMEAR = -5, which is not influenced by SIGMA.
- Fixed `mp_metagga_relax_flow` to use a `#!Python @flow` decorator instead of `#!Python @job`
- Fixed the Q-Chem Quasi-IRC job to run as one `#!Python @job` instead of two.

## [0.2.3]

### Added

- Added new defect EMT workflows (@rwexler)
- Added new defect utilities (@rwexler)
- Added a custom Q-Chem calculator based on Pymatgen and Custodian. (@samblau)
- Added Q-chem core recipes. (@samblau)
- Added the ability to pass option `run_kwargs` to the `.run()` method of the ASE optimizers.

### Changed

- Removed the need to call `ct.dispatch` when launching Covalent workflows.
- Renamed `quacc.util` to `quacc.utils`
- Refactored and standardized the NewtonNet recipes to match the other recipes

### Fixed

- The `WORKFLOW_ENGINE` setting can now be set dynamically, as expected.

## [0.2.2]

### Changed

- Changed package handling in `pyproject.toml` to better handle pip installs.

## [0.2.1]

### Added

- Added NewtonNet recipes and better sella support (@kumaranu)

### Changed

- Standardized `relax_cell` to be `False` by default for all recipes.
- Update the default `SIGMA` and `ISMEAR` in `MPScanSet` to match the new values to be used in Atomate2.

### Fixed

- Fixed a bug on Windows where the trajectory file would not be closed after a relaxation, causing permission errors.

### Removed

- Removed atomate2 as a dependency.
- Removed experimental Prefect support.

## [0.2.0]

### Added

- Added a quacc global setting, `WORKFLOW_ENGINE`, to set the workflow manager.
- Added support for the new `covalent-hpc-plugin` in `pyproject.toml`.

### Changed

- Quacc recipes are now decorated with generic `#!Python @job`, `#!Python @subflow`, or `#!Python @flow` decorators to be workflow engine-agnostic.
- Covalent is now an optional dependency to allow the base `quacc` package to be dependency-light.
- Default VASP pseudopotentials changed to `setups_pbe54.yaml`.
- Changed `quacc.recipes.emt.jobflow` and `quacc.recipes.emt.prefect` to `quacc.recipes.emt._jobflow` and `quacc.recipes.emt._prefect`

### Fixed

- Set `LMAXMIX` based on the `Z` value, not the s/p/d/f-block type.
- Do not set automatically `LMAXTAU` to 8 for f-containing elements in `Vasp` calculator.

### Removed

- Removed `quacc.recipes.emt.parsl` since it is now obsolete.
- Removed `quacc config` command-line option.

## [0.1.3]

### Added

- Added a `PRIMARY_STORE` quacc setting that, when specified, will automatically store all results in the specified Maggma store.

### Changed

- The trajectory is now stored in `quacc.schemas.cclib.summarize_run`.
- By default, results are now stored in a fixed `RESULTS_DIR`, which defaults to the current working directory.

### Fixed

- Fix path-related issues when running in local multi-threaded mode.
- Psi4 recipes now use `uks` for unrestricted calculations instead of `uhf`.

## [0.1.2]

### Added

- Added support for Prefect.
- Added `quacc.wflow_tools` module.

### Changed

- Made slab-related kwargs more consistent, such as by changing `slab_relax_electron`/`slab_relax_app` to just `slab_relax` regardless of workflow manager.

## [0.1.1]

### Added

- Added this `CHANGELOG.md` file.
- Added the `quacc.recipes.emt.parsl` module.
- Added a CLI for `quacc` along with a `quacc config` option to configure Covalent appropriately upon install.
- Added generic type hints for schemas.
- Added a `CREATE_UNIQUE_DIR` global setting to have quacc automatically make a unique working directory for each calculation.
- Added `CHECK_CONVERGENCE` to global settings.

### Changed

- The `quacc` directory is now found in a `src` basefolder.
- All recipes now support the `Atoms` object being passed in as an `AtomsSchema`.
- The `slab_relax_job` kwarg in `recipes.emt.slabs` and `recipes.vasp.slabs` workflows can no longer be set to `None`, as there are few situations where this would be desired.
- Class-based recipes have been converted to functions since they don't save state or have inheritance.

### Docs

- Switched the docs from Furo to Material for MkDocs.
- Expanded upon Parsl documentation.
- Modified tutorials and added example configs for Slurm.

### Fixed

- Temporary directories are cleaned up after the run is completed.

### Removed

- Removed `quacc.recipes.vasp.jobflow` module to prioritize Covalent and Parsl.

## [0.1.0]

See https://github.com/quantum-accelerators/quacc/releases/tag/v0.1.0 for more details.

## [0.0.6]

See https://github.com/quantum-accelerators/quacc/releases/tag/v0.0.6 for more details.

## [0.0.5]

See https://github.com/quantum-accelerators/quacc/releases/tag/v0.0.5 for more details.

## [0.0.4]

See https://github.com/quantum-accelerators/quacc/releases/tag/v0.0.4 for more details.

## [0.0.3]

See https://github.com/quantum-accelerators/quacc/releases/tag/v0.0.3 for more details.

## [0.0.2]

See https://github.com/quantum-accelerators/quacc/releases/tag/v0.0.2 for more details.

## [0.0.1]

See https://github.com/quantum-accelerators/quacc/releases/tag/v0.0.1 for more details.
