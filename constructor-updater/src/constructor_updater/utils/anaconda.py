"""Utilities for searching packages in `anaconda.org`."""

from functools import lru_cache
from typing import List

from constructor_updater.defaults import DEFAULT_CHANNEL
from constructor_updater.utils.request import get_request


@lru_cache
def conda_package_data(
    package_name: str,
    channel: str = DEFAULT_CHANNEL,
) -> dict:
    """Return information on package from given channel.

    Parameters
    ----------
    package_name : str
        Name of package.
    channel : str, optional
        Channel to search, by default `DEFAULT_CHANNEL`.

    Returns
    -------
    dict
        Package information.
    """
    url = f"https://api.anaconda.org/package/{channel}/{package_name}"
    response = get_request(url)
    return response.json()


@lru_cache
def conda_package_versions(
    package_name: str, channel: str = DEFAULT_CHANNEL
) -> List[str]:
    """Return information on package from given channel.

    Parameters
    ----------
    package_name : str
        Name of package.
    channel : str, optional
        Channel to search, by default `DEFAULT_CHANNEL`.

    Returns
    -------
    list of str
        Package versions.
    """
    return conda_package_data(
        package_name,
        channel=channel,
    ).get("versions", [])
