"""Conda utilities."""

import re
import sys
from pathlib import Path

from constructor_updater.defaults import (
    SENTINEL_FILE_PREFIX,
    SENTINEL_FILE_SUFFIX,
)


def normalized_name(name: str) -> str:
    """Normalize a package name.

    Replace underscores and dots by dashes and lower case it.

    Parameters
    ----------
    name : str
        The name of the package to normalize.

    Returns
    -------
    str
        The normalized package name.
    """
    return re.sub(r"[-_.]+", "-", name).lower()


def check_if_constructor_app(package_name, path=None) -> bool:
    """FIXME:"""
    if path is None:
        path = Path(sys.prefix)

    return (path.parent.parent / sentinel_file_name(package_name)).exists()


def sentinel_file_name(package_name):
    """Return the sentinel file name for a package.

    Parameters
    ----------
    package_name : str
        The name of the package to check for a sentinel file.

    Returns
    -------
    str
        The name of the sentinel file.
    """
    package_name = normalized_name(package_name)
    return SENTINEL_FILE_PREFIX + package_name + SENTINEL_FILE_SUFFIX


def check_if_conda_environment(path=None) -> bool:
    """Check if path is a conda environment.

    Parameters
    ----------
    path : str, optional
        If `None` then check if current process is running in a conda
        environment.

    Returns
    -------
    bool
    """
    if path is None:
        path = Path(sys.prefix)

    return (Path(path) / "conda-meta" / "history").exists()
