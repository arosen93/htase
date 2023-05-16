"""Recipes for slabs"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jobflow as jf
from ase import Atoms

from quacc.recipes.vasp.slabs import slab_relax_job as slab_relax_job_orig
from quacc.recipes.vasp.slabs import slab_relax_job as slab_static_job_orig
from quacc.util.slabs import make_max_slabs_from_bulk


@dataclass
class BulkToSlabsFlow(jf.Maker):
    """
    Workflow consisting of:
    1. Slab generation
    2. Slab relaxations (optional)
    3. Slab statics (optional)

    Parameters
    ----------
    name
        Name of the job.
    slab_relax_job
        Maker to use for the relaxation of the slab.
    slab_static_job
        Maker to use for the static calculation of the slab.
    relax_kwargs
        Additional keyword arguments to pass to the relaxation calculation.
    static_kwargs
        Additional keyword arguments to pass to the static calculation.
    """

    name: str = "VASP BulkToSlabsFlow"
    slab_relax_job: jf.Job | None = jf.job(slab_relax_job_orig)
    slab_static_job: jf.job | None = jf.job(slab_static_job_orig)
    relax_kwargs: dict[str, Any] | None = None
    static_kwargs: dict[str, Any] | None = None

    @jf.job
    def run(self, atoms: Atoms, slabgen_kwargs: dict[str, Any] = None) -> jf.Response:
        """
        Make the run.

        Parameters
        ----------
        atoms
            .Atoms object for the structure.
        slabgen_kwargs
            Additional keyword arguments to pass to make_max_slabs_from_bulk()

        Returns
        -------
        Response
            A Flow of relaxation and static jobs for the generated slabs.
        """

        relax_kwargs = self.relax_kwargs or {}
        static_kwargs = self.static_kwargs or {}
        slabgen_kwargs = slabgen_kwargs or {}

        # Generate all the slab
        slabs = make_max_slabs_from_bulk(atoms, **slabgen_kwargs)

        if not self.slab_relax_job and not self.slab_static_job:
            raise ValueError(
                "At least one of slab_relax_job or slab_static_job must be defined."
            )

        # Generate the jobs for each slab
        jobs = []
        outputs = []
        for slab in slabs:
            if self.slab_relax_job and self.slab_static_job:
                job1 = self.slab_relax_job(slab, **relax_kwargs)
                job2 = self.slab_static_job(job1.output["atoms"], **static_kwargs)
                jobs += [job1, job2]
                outputs.append(job2.output)
            elif self.slab_relax_job:
                job1 = self.slab_relax_job(slab, **relax_kwargs)
                jobs += [job1]
                outputs.append(job1.output)
            elif self.slab_static_job:
                job1 = self.slab_static_job(slab, **static_kwargs)
                jobs += [job1]
                outputs.append(job1.output)

        return jf.Response(
            output={"input_bulk": atoms, "generated_slabs": slabs},
            replace=jf.Flow(
                jobs,
                output=outputs,
                name=self.name,
            ),
        )
