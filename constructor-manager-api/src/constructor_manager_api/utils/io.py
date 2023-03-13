
from pathlib import Path

from constructor_manager_api.utils.conda import get_prefix_by_name


def get_config_path() -> Path:
    # path = get_prefix_by_name("base") / "var" / "constructor-manager"
    path = get_prefix_by_name("constructor-manager") / "var" / "constructor-manager-ui"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_settings_path(package_name) -> Path:
    # path = get_prefix_by_name("base") / "var" / "constructor-manager"
    path = get_config_path() / 'settings' / f"{package_name}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
