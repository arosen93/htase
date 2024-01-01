"""Utility functions for dealing with dictionaries."""
from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING
from collections.abc import MutableMapping

if TYPE_CHECKING:
    from typing import Any


def recursive_dict_merge(
    *args, remove_nones: bool = True, allowed_nones: list[Any] | None = None
) -> dict[str, Any]:
    """
    Recursively merge several dictionaries, taking the latter in the list as higher preference.
    It will also remove any keys that are None in the final, merged dictionary if `remove_nones`
    is True.

    Parameters
    ----------
    *args
        Dictionaries to merge
    remove_nones
        If True, recursively remove all items that are None in the final, merged dictionary.
    allowed_nones
        List of keys to never remove if `remove_nones` is True.

    Returns
    -------
    dict
        Merged dictionary
    """
    old_dict = args[0]
    for i in range(len(args) - 1):
        merged = _recursive_dict_pair_merge(old_dict, args[i + 1])
        old_dict = safe_dict_copy(merged)

    if remove_nones:
        merged = remove_dict_nones(merged, allowed_nones=allowed_nones)
    return merged


def _recursive_dict_pair_merge(
    dict1: MutableMapping[str, Any] | None, dict2: MutableMapping[str, Any] | None
) -> MutableMapping[str, Any]:
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

    dict1 = dict1 or (dict1.__class__() if dict1 is not None else {})
    dict2 = dict2 or (dict2.__class__() if dict2 is not None else {})
    merged = safe_dict_copy(dict1)

    for key, value in dict2.items():
        if key in merged:
            if isinstance(merged[key], MutableMapping) and isinstance(
                value, MutableMapping
            ):
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


def remove_dict_nones(
    start_dict: dict[str, Any], allowed_nones: list[Any] | None = None
) -> dict[str, Any]:
    """
    For a given dictionary, recursively remove all items that are None.

    Parameters
    ----------
    start_dict
        Dictionary to clean
    allowed_nones
        List of keys to never remove

    Returns
    -------
    dict
        Cleaned dictionary
    """

    if allowed_nones is None:
        allowed_nones = []
    if isinstance(start_dict, dict):
        return {
            k: remove_dict_nones(v, allowed_nones=allowed_nones)
            for k, v in start_dict.items()
            if (v is not None or k in allowed_nones)
        }
    return (
        [remove_dict_nones(v, allowed_nones=allowed_nones) for v in start_dict]
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
