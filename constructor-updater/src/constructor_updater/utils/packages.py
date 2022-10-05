"""
Convenience functions for searching packages in `pypi.org` and `anaconda.org`.
"""
import json
import re
from functools import lru_cache
from typing import List
from urllib.request import Request, urlopen

from constructor_updater import __version__


@lru_cache
def _user_agent() -> str:
    """Return a user agent string for use in http requests.

    Returns
    -------
    str
        User agent string.
    """
    return f"constructor-updater-{__version__}"


@lru_cache
def pypi_package_data(package_name: str) -> dict:
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
    with urlopen(Request(url, headers={"User-Agent": _user_agent()})) as resp:
        return json.load(resp)


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
    with urlopen(
        Request(
            f"https://pypi.org/simple/{package_name}",
            headers={"User-Agent": _user_agent()},
        )
    ) as resp:
        html = resp.read()

    return re.findall(f">{package_name}-(.+).tar", html.decode())


@lru_cache
def conda_package_data(package_name, channel="conda-forge"):
    """Return package information on package from given channel."""
    url = f"https://api.anaconda.org/package/{channel}/{package_name}"
    with urlopen(Request(url, headers={"User-Agent": _user_agent()})) as resp:
        return json.load(resp)


@lru_cache
def conda_package_versions(package_name: str, channel="conda-forge") -> List[str]:
    """ """
    return conda_package_data(package_name, channel=channel).get("versions", [])
