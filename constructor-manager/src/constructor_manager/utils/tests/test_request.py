from constructor_manager.utils.request import (
    _user_agent,
    get_request,
    plugin_versions,
)
from requests import Response


def test_user_agent():
    from constructor_manager_cli import __version__

    assert _user_agent() == f"constructor-manager-{__version__}"


def test_get_request():
    r = get_request("https://google.com")
    assert isinstance(r, Response)


def test_plugin_versions():
    data = plugin_versions("https://api.napari-hub.org/plugins")
    assert len(data) > 0
    assert "napari-svg" in data
