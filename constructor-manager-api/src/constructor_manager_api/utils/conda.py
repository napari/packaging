"""Conda utilities."""

import sys
from pathlib import Path
from typing import Optional


def get_base_prefix() -> Path:
    """Get base conda prefix.

    Returns
    -------
    pathlib.Path
        Base conda prefix.
    """
    current = Path(sys.prefix)
    if (current / "envs").exists() and (current / "envs").is_dir():
        return current

    if current.parent.name == "envs" and current.parent.is_dir():
        return current.parent.parent

    return current


def get_prefix_by_name(name: Optional[str] = None) -> Path:
    """Get conda prefix by environment name.

    This does not check if the environment exists.

    Parameters
    ----------
    name : str, optional
        Name of the environment. If `None` then return the current prefix.

    Returns
    -------
    pathlib.Path
        Conda prefix for the corresponding ``name``.
    """
    base_prefix = get_base_prefix()
    if name is None:
        return Path(sys.prefix)
    elif name == "base":
        return base_prefix
    else:
        return base_prefix / "envs" / name
