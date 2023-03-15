import os
import platform

from constructor_manager.utils.conda import get_base_prefix, get_prefix_by_name
from menuinst.api import _load, install, remove  # type: ignore

TEMPLATE = {
    "$schema": "https://json-schema.org/draft-07/schema",
    "$id": "https://schemas.conda.io/menuinst-1.schema.json",
    "menu_name": "",
    "menu_items": [],
}


def _locations(package_name, version, target_prefix=None):
    """Get the location of the shortcut for a package and version."""
    base_prefix = get_base_prefix()
    if target_prefix is None:
        target_prefix = get_prefix_by_name(f"{package_name}-{version}")

    metadata = _create_shortcut_metadata(package_name, version)
    _, menu_items = _load(metadata, target_prefix, base_prefix)
    locations = []
    for menu_item in menu_items:
        locations.append(menu_item.location)

    return locations


def _create_shortcut_metadata(
    package,
    version,
    command=None,
    description=None,
    categories=["Development"],
    icon_path_no_extension=None,
):
    """Create a shortcut metadata file for menuinst."""
    menu_name = f"{package} ({version})"
    metadata = TEMPLATE.copy()
    metadata["menu_name"] = menu_name

    menu_item = {
        "name": menu_name,
        "activate": True,
        "terminal": False,
        "platforms": {
            "win": {
                "desktop": True,
            },
            "linux": {"Categories": categories},
            "osx": {
                "CFBundleName": package,
                "CFBundleDisplayName": package,
                "CFBundleVersion": version,
            },
        },
    }
    if command:
        menu_item["command"] = command

    if description:
        menu_item["description"] = description

    if icon_path_no_extension:
        menu_item["icon"] = str(icon_path_no_extension) + ".{{ ICON_EXT }}"

    metadata["menu_items"] = [menu_item]
    return metadata


def _create_remove_shortcut(package, version, remove_action=False, target_prefix=None):
    """Create or remove shortcuts for a package and version.

    Parameters
    ----------
    package : str
        The name of the package.
    version : str
        The version of the package.
    remove_action : bool
        If True, remove the shortcuts. If False, create the shortcuts.

    Returns
    -------
    paths : list
        The paths to the shortcuts that were created.
    """
    if target_prefix is None:
        target_prefix = get_prefix_by_name(f"{package}-{version}")

    base_prefix = get_prefix_by_name("base")

    # TODO: Is this standard for all platforms?
    metadata_path = target_prefix / "Menu" / f"{package}-menu.json"
    func = remove if remove_action else install
    try:
        paths = func(
            metadata_path,
            target_prefix=target_prefix,
            base_prefix=base_prefix,
        )
    except Exception:
        paths = []

    return paths


def create_shortcut(package, version, target_prefix=None):
    """Create a shortcut for a package and version.

    Parameters
    ----------
    package : str
        The name of the package.
    version : str
        The version of the package.

    Returns
    -------
    paths : list
        The paths to the shortcuts that were created.
    """
    return _create_remove_shortcut(
        package, version, remove_action=False, target_prefix=target_prefix
    )


def remove_shortcut(package, version, target_prefix=None):
    """Remove a shortcut for a package and version.

    Parameters
    ----------
    package : str
        The name of the package.
    version : str
        The version of the package.

    Returns
    -------
    paths : list
        The paths to the shortcuts that were removed.
    """
    return _create_remove_shortcut(
        package, version, remove_action=True, target_prefix=target_prefix
    )


def open_application(package, version, target_prefix=None):
    """Open the application using the shortcuts created by menuinst.

    Parameters
    ----------
    package : str
        The name of the package.
    version : str
        The version of the package.
    target_prefix : str, optional
        The target prefix to use. If not provided, the default is used.

    Returns
    -------
    ret_code : int
        The return code from the command that opened the application.
    """
    paths = _locations(package, version, target_prefix=target_prefix)
    if paths:
        path = paths[0]

    plat = platform.system()
    if plat == "Darwin":
        ret_code = os.system(f"open '{path}'")
    elif plat == "Linux":
        cmd = ""
        with open(path) as fh:
            for line in fh:
                if line.startswith("Exec="):
                    cmd = line.split("=", 1)[1].strip()
        if cmd:
            ret_code = os.system(cmd)
    elif plat == "Windows":
        ret_code = os.startfile(path)

    return ret_code
