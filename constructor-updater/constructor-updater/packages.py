"""
Convenience functions for searching packages in pypi.org and anaconda.org.
"""
import json
from functools import lru_cache
from urllib.request import Request, urlopen


@lru_cache
def _user_agent() -> str:
    """Return a user agent string for use in http requests."""
    return "conda constructor updater"


@lru_cache
def pypi_package(package_name):
    """Return"""
    url = f"https://pypi.org/pypi/{package_name}/json"
    with urlopen(Request(url, headers={'User-Agent': _user_agent()})) as resp:
        return json.load(resp)


@lru_cache
def conda_package(package_name, channel="conda-forge"):
    """Return"""
    url = f"https://api.anaconda.org/package/{channel}/{package_name}"
    with urlopen(Request(url, headers={'User-Agent': _user_agent()})) as resp:
        return json.load(resp)
