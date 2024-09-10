"""Workflow decorators."""

from __future__ import annotations

from functools import partial, wraps
from typing import TYPE_CHECKING, Any, Callable

from quacc.settings import change_settings_wrap, nest_results_dir_wrap

if TYPE_CHECKING:
    from prefect import Flow as PrefectFlow

Job = Callable[..., Any]
Flow = Callable[..., Any]
Subflow = Callable[..., Any]

if TYPE_CHECKING:
    from importlib.util import find_spec

    from quacc.settings import QuaccSettings

    if bool(find_spec("prefect")):
        from prefect import Task


def job(_func: Callable[..., Any] | None = None, **kwargs) -> Job:
    """
    Decorator for individual compute jobs. This is a `#!Python @job` decorator. Think of
    each `#!Python @job`-decorated function as an individual SLURM job, if that helps.

    | Quacc | Covalent      | Parsl        | Dask      | Prefect | Redun  | Jobflow |
    | ----- | ------------- | ------------ | --------- | ------- | ------ | ------- |
    | `job` | `ct.electron` | `python_app` | `delayed` | `task`  | `task` | `job`   |

    All `#!Python @job`-decorated functions are transformed into their corresponding
    decorator.

    ```python
    from quacc import job


    @job
    def add(a, b):
        return a + b


    add(1, 2)
    ```

    ... is the same as doing

    === "Covalent"

        ```python
        import covalent as ct


        @ct.electron
        def add(a, b):
            return a + b


        add(1, 2)
        ```

    === "Dask"

        ```python
        from dask import delayed


        @delayed
        def add(a, b):
            return a + b


        add(1, 2)
        ```

    === "Parsl"

        ```python
        from parsl import python_app


        @python_app
        def add(a, b):
            return a + b


        add(1, 2)
        ```

    === "Prefect"

        ```python
        from prefect import task


        @task
        def add(a, b):
            return a + b


        add.submit(1, 2)
        ```

    === "Redun"

        ```python
        from redun import task


        @task
        def add(a, b):
            return a + b


        add(1, 2)
        ```

    === "Jobflow"

        ```python
        import jobflow as jf


        @jf.job
        def add(a, b):
            return a + b


        add(1, 2)
        ```

    Parameters
    ----------
    _func
        The function to decorate. This is not meant to be supplied by the user.
    **kwargs
        Keyword arguments to pass to the workflow engine decorator.

    Returns
    -------
    Job
        The @job-decorated function.
    """
    from quacc import get_settings

    settings = get_settings()

    if _func is None:
        return partial(job, **kwargs)

    if changes := kwargs.pop("settings_swap", {}):
        return job(change_settings_wrap(_func, changes), **kwargs)

    if settings.WORKFLOW_ENGINE == "covalent":
        import covalent as ct

        return ct.electron(_func, **kwargs)
    elif settings.WORKFLOW_ENGINE == "dask":
        from dask import delayed

        # See https://github.com/dask/dask/issues/10733

        @wraps(_func)
        def wrapper(*f_args, **f_kwargs):
            return _func(*f_args, **f_kwargs)

        return Delayed_(delayed(wrapper, **kwargs))
    elif settings.WORKFLOW_ENGINE == "jobflow":
        from jobflow import job as jf_job

        return jf_job(_func, **kwargs)
    elif settings.WORKFLOW_ENGINE == "parsl":
        from parsl import python_app

        wrapped_fn = _get_parsl_wrapped_func(_func, kwargs)

        return python_app(wrapped_fn, **kwargs)
    elif settings.WORKFLOW_ENGINE == "redun":
        from redun import task

        return task(_func, namespace=_func.__module__, **kwargs)
    elif settings.WORKFLOW_ENGINE == "prefect":
        return _decorate_prefect_job(_func, kwargs, settings)
    else:
        return _func


def flow(_func: Callable[..., Any] | None = None, **kwargs) -> Flow:
    """
    Decorator for workflows, which consist of at least one compute job. This is a
    `#!Python @flow` decorator.

    | Quacc  | Covalent     | Parsl     | Dask      | Prefect | Redun  | Jobflow   |
    | ------ | ------------ | --------- | --------- | ------- | ------ | --------- |
    | `flow` | `ct.lattice` | No effect | No effect | `flow`  | `task` | No effect |

    All `#!Python @flow`-decorated functions are transformed into their corresponding
    decorator.

    ```python
    from quacc import flow, job


    @job
    def add(a, b):
        return a + b


    @flow
    def workflow(a, b, c):
        return add(add(a, b), c)


    workflow(1, 2, 3)
    ```

    ... is the same as doing

    === "Covalent"

        ```python
        import covalent as ct


        @ct.electron
        def add(a, b):
            return a + b


        @ct.lattice
        def workflow(a, b, c):
            return add(add(a, b), c)


        workflow(1, 2, 3)
        ```

    === "Dask"

        ```python
        from dask import delayed


        @delayed
        def add(a, b):
            return a + b


        def workflow(a, b, c):
            return add(add(a, b), c)


        workflow(1, 2, 3)
        ```

    === "Parsl"

        ```python
        from parsl import python_app


        @python_app
        def add(a, b):
            return a + b


        def workflow(a, b, c):
            return add(add(a, b), c)


        workflow(1, 2, 3)
        ```

    === "Prefect"

        ```python
        from prefect import flow, task


        @task
        def add(a, b):
            return a + b


        @flow
        def workflow(a, b, c):
            return add.submit(add.submit(a, b), c)


        workflow(1, 2, 3)
        ```

    === "Redun"

        ```python
        from redun import task


        @task
        def add(a, b):
            return a + b


        @task
        def workflow(a, b, c):
            return add(add(a, b), c)


        workflow(1, 2, 3)
        ```

    === "Jobflow"

        !!! Warning

            This decorator is not meant to be used with Jobflow at this time.

    Parameters
    ----------
    _func
        The function to decorate. This is not meant to be supplied by the user.
    **kwargs
        Keyword arguments to pass to the decorator.

    Returns
    -------
    Flow
        The `#!Python @flow`-decorated function.
    """
    from quacc import get_settings

    settings = get_settings()

    if _func is None:
        return partial(flow, **kwargs)

    elif settings.WORKFLOW_ENGINE == "covalent":
        import covalent as ct

        return ct.lattice(_func, **kwargs)
    elif settings.WORKFLOW_ENGINE == "redun":
        from redun import task

        return task(_func, namespace=_func.__module__, **kwargs)
    elif settings.WORKFLOW_ENGINE == "prefect":
        return _decorate_prefect_flow_subflow(_func, kwargs, settings)

    else:
        return _func


def subflow(_func: Callable[..., Any] | None = None, **kwargs) -> Subflow:
    """
    Decorator for (dynamic) sub-workflows. This is a `#!Python @subflow` decorator.

    | Quacc     | Covalent                  | Parsl      | Dask      | Prefect | Redun  | Jobflow   |
    | --------- | ------------------------- | ---------- | --------- | ------- |------- | --------- |
    | `subflow` | `ct.electron(ct.lattice)` | `join_app` | `delayed` | `flow`  | `task` | No effect |

    All `#!Python @subflow`-decorated functions are transformed into their corresponding
    decorator.

    ```python
    import random
    from quacc import flow, job, subflow


    @job
    def add(a, b):
        return a + b


    @job
    def make_more(val):
        return [val] * random.randint(2, 5)


    @subflow
    def add_distributed(vals, c):
        return [add(val, c) for val in vals]


    @flow
    def workflow(a, b, c):
        result1 = add(a, b)
        result2 = make_more(result1)
        return add_distributed(result2, c)


    workflow(1, 2, 3)
    ```

    ... is the same as doing

    === "Covalent"

        ```python
        import random
        import covalent as ct


        @ct.electron
        def add(a, b):
            return a + b


        @ct.electron
        def make_more(val):
            return [val] * random.randint(2, 5)


        @ct.electron
        @ct.lattice
        def add_distributed(vals, c):
            return [add(val, c) for val in vals]


        @ct.lattice
        def workflow(a, b, c):
            result1 = add(a, b)
            result2 = make_more(result1)
            return add_distributed(result2, c)


        workflow(1, 2, 3)
        ```

    === "Dask"

        It's complicated... see the source code.

    === "Parsl"

        ```python
        import random
        from parsl import join_app, python_app


        @python_app
        def add(a, b):
            return a + b


        @python_app
        def make_more(val):
            return [val] * random.randint(2, 5)


        @join_app
        def add_distributed(vals, c):
            return [add(val, c) for val in vals]


        def workflow(a, b, c):
            result1 = add(a, b)
            result2 = make_more(result1)
            return add_distributed(result2, c)


        workflow(1, 2, 3)
        ```

    === "Prefect"

        ```python
        import random
        from prefect import flow, task


        @task
        def add(a, b):
            return a + b


        @task
        def make_more(val):
            return [val] * random.randint(2, 5)


        @flow
        def add_distributed(vals, c):
            return [add.submit(val, c) for val in vals]


        @flow
        def workflow(a, b, c):
            result1 = add.submit(a, b)
            result2 = make_more.submit(result1)
            return add_distributed(result2, c)


        workflow(1, 2, 3)
        ```

    === "Redun"

        ```python
        import random
        from redun import task


        @task
        def add(a, b):
            return a + b


        @task
        def make_more(val):
            return [val] * random.randint(2, 5)


        @task
        def add_distributed(vals, c):
            return [add(val, c) for val in vals]


        @task
        def workflow(a, b, c):
            result1 = add(a, b)
            result2 = make_more(result1)
            return add_distributed(result2, c)


        workflow(1, 2, 3)
        ```

    === "Jobflow"

        !!! Warning

            This decorator is not meant to be used with Jobflow at this time.

    Parameters
    ----------
    _func
        The function to decorate. This is not meant to be supplied by the user.
    **kwargs
        Keyword arguments to pass to the decorator.

    Returns
    -------
    callable
        The decorated function.
    """
    from quacc import get_settings

    settings = get_settings()

    if _func is None:
        return partial(subflow, **kwargs)

    elif settings.WORKFLOW_ENGINE == "covalent":
        import covalent as ct

        return ct.electron(ct.lattice(_func), **kwargs)
    elif settings.WORKFLOW_ENGINE == "dask":
        from dask import delayed
        from dask.distributed import worker_client

        # See https://github.com/dask/dask/issues/10733

        @wraps(_func)
        def wrapper(*f_args, **f_kwargs):
            with worker_client() as client:
                futures = client.compute(_func(*f_args, **f_kwargs))
                return client.gather(futures)

        return delayed(wrapper, **kwargs)
    elif settings.WORKFLOW_ENGINE == "parsl":
        from parsl import join_app

        wrapped_fn = _get_parsl_wrapped_func(_func, kwargs)

        return join_app(wrapped_fn, **kwargs)
    elif settings.WORKFLOW_ENGINE == "prefect":
        return _decorate_prefect_flow_subflow(_func, kwargs, settings)

    elif settings.WORKFLOW_ENGINE == "redun":
        from redun import task

        return task(_func, namespace=_func.__module__, **kwargs)
    else:
        return _func


def _decorate_prefect_job(
    _func: Callable, kwargs: dict[str, Any], settings: QuaccSettings
) -> Task:
    from prefect import task

    if settings.PREFECT_AUTO_SUBMIT or settings.NESTED_RESULTS_DIR:

        @wraps(_func)
        def wrapper(*f_args, **f_kwargs):
            if settings.NESTED_RESULTS_DIR:
                decorated = task(nest_results_dir_wrap(_func), **kwargs)
            else:
                decorated = task(_func, **kwargs)
            if settings.PREFECT_AUTO_SUBMIT:
                return decorated.submit(*f_args, **f_kwargs)
            else:
                return decorated(*f_args, **f_kwargs)

        return wrapper
    else:
        return task(_func, **kwargs)


def _decorate_prefect_flow_subflow(
    _func: Callable, kwargs: dict[str, Any], settings: QuaccSettings
) -> PrefectFlow:
    from prefect import flow as prefect_flow

    if settings.NESTED_RESULTS_DIR:

        @wraps(_func)
        def wrapper(*f_args, **f_kwargs):
            decorated = prefect_flow(
                nest_results_dir_wrap(_func), validate_parameters=False, **kwargs
            )
            return decorated(*f_args, **f_kwargs)

        return wrapper
    else:
        return prefect_flow(_func, validate_parameters=False, **kwargs)


def _get_parsl_wrapped_func(
    func: Callable, decorator_kwargs: dict[str, Any]
) -> Callable:
    """
    Wrap a function to handle special Parsl arguments.

    Parameters
    ----------
    func
        The function to wrap.
    decorator_kwargs
        Decorator keyword arguments, including Parsl-specific ones that
        are meant to be passed to the underlying function. The `walltime`
        and `parsl_resource_specification` arguments will be injected
        into the function call and removed from the decorator arguments.

    Returns
    -------
    callable
        The wrapped function.
    """
    walltime = decorator_kwargs.pop("walltime", None)
    parsl_resource_specification = decorator_kwargs.pop(
        "parsl_resource_specification", {}
    )

    def wrapper(
        *f_args,
        walltime=walltime,  # noqa: ARG001
        parsl_resource_specification=parsl_resource_specification,  # noqa: ARG001
        **f_kwargs,
    ):
        return func(*f_args, **f_kwargs)

    if getattr(func, "_changed", False):
        wrapper._changed = func._changed  # type: ignore[attr-defined]
        wrapper._original_func = func._original_func  # type: ignore[attr-defined]
    wrapper.__name__ = func.__name__
    return wrapper


class Delayed_:
    """A small Dask-compatible, serializable object to wrap delayed functions that we
    don't want to execute.
    """

    __slots__ = ("func",)

    def __init__(self, func):
        self.func = func

    def __reduce__(self):
        return (Delayed_, (self.func,))

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
