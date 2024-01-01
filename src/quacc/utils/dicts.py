"""Utility functions for dealing with dictionaries."""
from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from quacc import Remove

if TYPE_CHECKING:
    from typing import Any


def recursive_dict_merge(*args) -> dict[str, Any]:
    """
    Recursively merge several dictionaries, taking the latter in the list as higher preference.
    Also removes any entries that are `quacc.Remove` from the final dictionary.

    Parameters
    ----------
    *args
        Dictionaries to merge

    Returns
    -------
    dict
        Merged dictionary
    """
    old_dict = args[0]
    for i in range(len(args) - 1):
        merged = _recursive_dict_pair_merge(old_dict, args[i + 1])
        old_dict = safe_dict_copy(merged)

    return remove_dict_entries(merged, Remove)


def _recursive_dict_pair_merge(
    dict1: dict[str, Any] | None, dict2: dict[str, Any] | None
) -> dict[str, Any]:
    """
    Recursively merges two dictionaries. If one of the inputs is `None`, then it is
    treated as `{}`.

    This function should be used instead of the | operator when merging nested dictionaries,
    e.g. `{"a": {"b": 1}} | {"a": {"c": 2}}` will return `{"a": {"c": 2}}` whereas
    `recursive_dict_merge({"a": {"b": 1}}, {"a": {"c": 2}})` will return `{"a": {"b": 1, "c": 2}}`.

    Parameters
    ----------
    dict1
        First dictionary
    dict2
        Second dictionary

    Returns
    -------
    dict
        Merged dictionary
    """
    dict1 = dict1 or {}
    dict2 = dict2 or {}
    merged = safe_dict_copy(dict1)

    for key, value in dict2.items():
        if key in merged:
            if isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = _recursive_dict_pair_merge(merged[key], value)
            else:
                merged[key] = value
        else:
            merged[key] = value

    return merged


def safe_dict_copy(d: dict) -> dict:
    """
    Safely copy a dictionary to account for deepcopy errors.

    Parameters
    ----------
    d
        Dictionary to copy

    Returns
    -------
    dict
        Copied dictionary
    """
    try:
        return deepcopy(d)
    except Exception:
        return d.copy()


def remove_dict_entries(
    start_dict: dict[str, Any], remove_trigger: Any
) -> dict[str, Any]:
    """
    For a given dictionary, recursively remove all items that are None.

    Parameters
    ----------
    start_dict
        Dictionary to clean
    remove_trigger
        Value to that triggers removal of the entry

    Returns
    -------
    dict
        Cleaned dictionary
    """

    if isinstance(start_dict, dict):
        return {
            k: remove_dict_entries(v, remove_trigger)
            for k, v in start_dict.items()
            if v is not remove_trigger
        }
    return (
        [remove_dict_entries(v, remove_trigger) for v in start_dict]
        if isinstance(start_dict, list)
        else start_dict
    )


def sort_dict(start_dict: dict[str, Any]) -> dict[str, Any]:
    """
    For a given dictionary, recursively sort all entries alphabetically by key.

    Parameters
    ----------
    start_dict
        Dictionary to sort

    Returns
    -------
    dict
        Sorted dictionary
    """

    return {
        k: sort_dict(v) if isinstance(v, dict) else v
        for k, v in sorted(start_dict.items())
    }


def clean_task_doc(start_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Clean up a task document dictionary by removing all entries
    that are None and sorting the dictionary alphabetically by key.

    Parameters
    ----------
    start_dict
        Dictionary to clean

    Returns
    -------
    dict
        Cleaned dictionary
    """
    return sort_dict(remove_dict_entries(start_dict, None))
