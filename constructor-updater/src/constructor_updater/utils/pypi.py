"""Convenience functions for searching packages in `pypi.org`."""

import re
from functools import lru_cache
from typing import List

from constructor_updater.utils.request import get_request


@lru_cache
def pypi_package_data(package_name : str) -> dict:
    """Return package information on package.

    Parameters
    ----------
    package_name : str
        Name of package.

    Returns
    -------
    dict
        Package information.
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    return get_request(url).json()


@lru_cache
def pypi_package_versions(package_name: str) -> List[str]:
    """Get available versions of a package on pypi.

    Parameters
    ----------
    package_name : str
        Name of the package.

    Returns
    -------
    list
        Versions available on pypi.
    """
    url = f"https://pypi.org/simple/{package_name}"
    html = get_request(url).text
    return re.findall(f'>{package_name}-(.+).tar', html.decode())
