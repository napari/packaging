from functools import lru_cache

import requests
from constructor_updater_cli import __version__
from constructor_updater_cli.defaults import DEFAULT_TIMEOUT


@lru_cache
def _user_agent() -> str:
    """Return a user agent string for use in http requests.

    Returns
    -------
    str
        User agent string.
    """
    return f"constructor-updater-{__version__}"


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
