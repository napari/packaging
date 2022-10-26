"""Package utilities, name normalization and sentinel files."""

import re

from constructor_manager_cli.defaults import (
    SENTINEL_FILE_PREFIX,
    SENTINEL_FILE_SUFFIX,
)


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


def get_package_spec(package, version, build):
    """Return the package spec for a package.

    Parameters
    ----------
    package : str
        The name of the package.
    version : str
        The version of the package.
    build : str
        The build string of the package.

    Returns
    -------
    str
        The package spec.
    """
    spec = f"{package}=={version}"
    if build:
        spec = spec + f"=*{build}*"

    return spec
