"""
Utility functions for dealing with dictionaries
"""
from __future__ import annotations


def merge_dicts(dict1: dict, dict2: dict, remove_empties: bool = False) -> dict:
    """
    Merge two dictionaries recursively.

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

    merged = dict1.copy()
    for k, v in dict2.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = merge_dicts(merged[k], v)
        else:
            merged[k] = v
    if remove_empties:
        merged = remove_dict_empties(merged)

    return merged


def clean_dict(start_dict: dict, remove_empties: bool = False) -> dict:
    """
    For a given dictionary, recursively remove all items that are None
    or are empty lists/dicts, and then sort all entries alphabetically by key.

    Parameters
    ----------
    start_dict
        Dictionary to clean
    remove_empties
        If True, remove empty lists and dictionaries

    Returns
    -------
    dict
        Cleaned and sorted dictionary
    """

    if remove_empties:
        start_dict = remove_dict_empties(start_dict)
    return sort_dict(start_dict)


def remove_dict_empties(start_dict: dict) -> dict:
    """
    For a given dictionary, recursively remove all items that are None
    or are empty lists/dicts.

    Parameters
    ----------
    start_dict
        Dictionary to clean

    Returns
    -------
    dict
        Cleaned dictionary
    """

    if isinstance(start_dict, dict):
        return {
            k: remove_dict_empties(v)
            for k, v in start_dict.items()
            if v is not None and (not isinstance(v, (dict, list)) or len(v) != 0)
        }
    return (
        [remove_dict_empties(v) for v in start_dict]
        if isinstance(start_dict, list)
        else start_dict
    )


def sort_dict(start_dict: dict) -> dict:
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
