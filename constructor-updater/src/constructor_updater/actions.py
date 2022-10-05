"""Constructor updater actions."""

import subprocess
from typing import Dict

from constructor_updater.defaults import DEFAULT_CHANNEL
from constructor_updater.installer import CondaInstaller
from constructor_updater.utils.anaconda import conda_package_versions
from constructor_updater.utils.io import get_installed_versions
from constructor_updater.utils.versions import is_stable_version, parse_version


def _create_with_plugins():
    """Update the package."""
    pass


def _create_with_plugins_one_by_one():
    """Update the package."""
    pass


def _execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def check_updates(
    package_name : str,
    current_version : str,
    stable: bool = True,
    channel: str = DEFAULT_CHANNEL,
) -> Dict:
    """Check for package updates.

    Parameters
    ----------
    current_verison : str
        The current version of the package to check for updates.
    stable : bool, optional
        If ``True``, check for stable versions. Default is ``True``.
    channel : str, optional
        Check for available versions on this channel. Default is ``conda-forge``.

    Returns
    -------
    dict
        Dictionary containing the current and latest versions, found
        installed versions and the installer type used.
    """
    versions = conda_package_versions(package_name, channel=channel)
    if stable:
        versions = list(filter(is_stable_version, versions))

    update = False
    latest_version = versions[-1] if versions else None
    installed_versions_builds = get_installed_versions(package_name)
    installed_versions = [vb[0] for vb in installed_versions_builds]
    update = (
        parse_version(latest_version) > parse_version(current_version)
        and latest_version not in installed_versions
    )

    return {
        "available_versions": versions,
        "current_version": current_version,
        "latest_version": latest_version,
        "found_versions": installed_versions,
        "update": update,
    }


def update():
    """Update the package."""
    pass
    # Try with all plugins
    # Try with one by one plugins

    # Must print results iteratively 
    # Example
    for path in _execute(["locate", "a"]):
        print(path, end="")


def clean_all():
    """Remove any broken environments."""


def clean():
    """Update the package."""
    pass


package_name = "napari"
current_version = "0.4.16"
# data = conda_package_versions(package_name)
# data = pypi_package_versions(package_name)

# for item in data:
#     print(item, _is_stable_version(item))


print(check_updates(package_name, current_version, stable=False, channel=package_name))
