"""Conda utilities."""

import sys
from pathlib import Path
from typing import Optional, Tuple

from conda.models.match_spec import MatchSpec  # type: ignore


def parse_conda_version_spec(package: str) -> Tuple[str, str, str]:
    """Parse a conda version spec into a tuple of (name, version).

    Parameters
    ----------
    package : str
        The package name and version spec.

    Returns
    -------
    tuple
        The package name and version.
    """
    package_spec = MatchSpec(package)
    parts = package_spec.conda_build_form().split(" ")
    package_name = package_spec.name
    version = ""
    build_string = ""
    if len(parts) == 2:
        version, build_string = parts[1], ""
    elif len(parts) == 3:
        version, build_string = parts[1:]

    if version:
        version = version.rstrip(".*")  # ?
        version = version.rstrip("*")  # ?
    else:
        version = ""

    return package_name, version, build_string


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
