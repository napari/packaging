"""Utilities for searching packages in `anaconda.org`."""

import re
from functools import lru_cache
from typing import List, Optional

from constructor_manager_cli.defaults import DEFAULT_CHANNEL
from constructor_manager_cli.utils.request import get_request
from constructor_manager_cli.utils.versions import sort_versions


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
        Channels to search, by default `DEFAULT_CHANNEL`.

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
    package_name: str,
    build: Optional[str] = None,
    channels: List[str] = [DEFAULT_CHANNEL],
    reverse: bool = False,
) -> List[str]:
    """Return information on package from given channel.

    Parameters
    ----------
    package_name : str
        Name of package.
    build: str
        Filter by build string, e.g. ``'*pyside*'``.
    channels : list of str, optional
        Channels to search, by default `[DEFAULT_CHANNEL]`.
    reverse : bool, optional
        Sort versions in reverse order, by default `False`.

    Returns
    -------
    list of str
        Package versions.
    """
    if build:
        pat = re.compile(build.replace("*", ".*"))

    versions = []
    for channel in channels:
        if build:
            files = conda_package_data(
                package_name,
                channel=channel,
            ).get("files", [])

            for file_data in files:
                build_string = file_data.get("attrs", {}).get("build")
                if pat.search(build_string):
                    version = file_data.get("version", "")
                    if version and version not in versions:
                        versions.append(version)
        else:
            versions.extend(
                conda_package_data(
                    package_name,
                    channel=channel,
                ).get("versions", [])
            )

    return sort_versions(set(versions), reverse=reverse)
