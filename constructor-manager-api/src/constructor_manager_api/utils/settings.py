"""Constuctor manager."""

from typing import Any, Dict

import yaml

from constructor_manager_api.utils.io import get_settings_path


_default_settings = {  # type: ignore
    "current_version": None,
    "build_string": None,
    "plugins_url": None,
    "channels": [],
    "log": None,
    "dev": None,
}


def save_settings(package_name: str, settings: Dict[str, Any]) -> None:
    """"Save constructor manager settings to file per `package_name`.""" ""
    path = get_settings_path(package_name)
    with open(path, "w") as f:
        yaml.dump(settings, f)


def load_settings(package_name: str):
    """"Load constructor manager settings from file per `package_name`.""" ""
    path = get_settings_path(package_name)
    loaded_settings = _default_settings.copy()
    if path.exists():
        with open(path) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        loaded_settings.update(data)

    return loaded_settings
