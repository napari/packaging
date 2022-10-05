"""Constructor updater actions."""

import shutil
from typing import Dict

from constructor_updater.defaults import DEFAULT_CHANNEL
from constructor_updater.installer import CondaInstaller
from constructor_updater.utils.anaconda import conda_package_versions
from constructor_updater.utils.conda import get_prefix_by_name
from constructor_updater.utils.io import get_installed_versions, create_sentinel_file, get_broken_envs, remove_sentinel_file
from constructor_updater.utils.versions import is_stable_version, parse_version


def _create_with_plugins(package_name, package_version, build, plugins):
    """Update the package."""
    prefix = get_prefix_by_name(f'{package_name}-{package_version}')
    installer = CondaInstaller(pinned=f"{package_name}={package_version}")
    spec = f"{package_name}=={package_version}"
    if build:
        spec = spec + f"=*{build}*"

    job_id = installer.create([spec] + plugins, prefix=prefix)
    return installer._exit_codes[job_id]


def _create_with_plugins_one_by_one(package_name, package_version, build, plugins):
    """Update the package."""
    prefix = get_prefix_by_name(f'{package_name}-{package_version}')
    installer = CondaInstaller(pinned=f"{package_name}={package_version}")
    spec = f"{package_name}=={package_version}"
    if build:
        spec = spec + f"=*{build}*"

    job_id = installer.create([spec], prefix=prefix)
    for plugin in plugins:
        installer.install([plugin], prefix=prefix)

    return installer._exit_codes[job_id]
    

def check_updates(
    package_name: str,
    current_version: str,
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
    update = parse_version(latest_version) > parse_version(current_version)

    return {
        "available_versions": versions,
        "current_version": current_version,
        "latest_version": latest_version,
        "found_versions": installed_versions,
        "update": update,
        "installed": latest_version in installed_versions,
    }


def update(package_name, package_version, build, plugins):
    """Update the package."""
    return_code = _create_with_plugins(package_name, package_version, build, plugins)

    if bool(return_code):
        return_code = _create_with_plugins_one_by_one(package_name, package_version, build, plugins)

    if not bool(return_code):
        create_sentinel_file(package_name, package_version)

    print("finished!")


def clean_all(package_name):
    """Clean all environments of a given package.

    Environments will be removed using conda/mamba, or the folders deleted in
    case conda fails.

    Parameters
    ----------
    package_name : str
        Name of the package.
    """
    # Try to remove using conda/mamba
    installer = CondaInstaller()
    failed = []
    for prefix in get_broken_envs(package_name):
        job_id = installer.remove(prefix)
        if installer._exit_codes[job_id]:
            failed.append(prefix)

    # Otherwise remove the folders manually
    for prefix in failed:
        print("removing", prefix)
        # shutil.rmtree(path)


def check_updates_and_clean(package_name, current_version, stable, channel):
    """Check for updates and clean."""
    res = check_updates(package_name, current_version, stable, channel)
    if res["installed"]:
        remove_sentinel_file(package_name, current_version)

    clean_all(package_name)


# update("napari", "0.4.16", "pyside", ["napari-arboretum"])
print(check_updates("napari", "0.4.15", stable=True, channel="conda-forge"))
# clean_all("napari")
