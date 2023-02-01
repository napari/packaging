"""Package utilities, name normalization and sentinel files."""

import re
import logging

from constructor_manager_cli.defaults import (
    SENTINEL_FILE_PREFIX,
    SENTINEL_FILE_SUFFIX,
)


logger = logging.getLogger(__name__)


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
