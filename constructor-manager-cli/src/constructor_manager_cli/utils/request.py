from functools import lru_cache
from typing import List

import requests

from constructor_manager_cli import __version__
from constructor_manager_cli.defaults import DEFAULT_TIMEOUT


@lru_cache
def _user_agent() -> str:
    """Return a user agent string for use in http requests.

    Returns
    -------
    str
        User agent string.
    """
    return f"constructor-manager-{__version__}"


def get_request(url: str) -> requests.Response:
    """Return a requests session with a user agent.

    Parameters
    ----------
    url : str
        URL to request.

    Returns
    -------
    requests.Response
        Response object.
    """
    session = requests.Session()
    session.headers.update({"user-agent": _user_agent()})
    return session.get(url, timeout=DEFAULT_TIMEOUT)


@lru_cache
def plugin_versions(
    url: str,
) -> List[str]:
    """Return information on package plugins from endpoint in json.

    Parameters
    ----------
    url : str
        Url to json endpoint.

    Returns
    -------
    list of str
        Package versions.
    """
    response = get_request(url)

    data = response.json()
    if isinstance(data, dict):
        data = data.keys()

    plugins = []
    for item in data:
        plugins.append(item.lower())

    return list(sorted(plugins))
