from pathlib import Path

from constructor_manager_api.utils.conda import get_prefix_by_name


def get_config_path() -> Path:
    """Get the path to the constructor-manager-ui config directory."""
    path = get_prefix_by_name("constructor-manager") / "var" / "constructor-manager-ui"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_settings_path(package_name: str) -> Path:
    """Get the path to the settings file for a package."""
    path = get_config_path() / "settings" / f"{package_name}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
