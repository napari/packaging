"""Constructor updater actions."""

import os
import shutil
from typing import Dict, List

from conda.models.match_spec import MatchSpec  # type: ignore

from constructor_updater.defaults import DEFAULT_CHANNEL
from constructor_updater.installer import CondaInstaller
from constructor_updater.utils.anaconda import conda_package_versions
from constructor_updater.utils.conda import get_prefix_by_name
from constructor_updater.utils.io import (
    create_sentinel_file,
    get_broken_envs,
    get_installed_versions,
    remove_sentinel_file,
)
from constructor_updater.utils.versions import is_stable_version, parse_version


def _create_with_plugins(
    package,
    plugins,
    channel,
):
    """Update the package."""
    package_spec = MatchSpec(package)
    prefix = get_prefix_by_name(f"{package_spec.name}-{package_spec.version}")
    installer = CondaInstaller(
        pinned=f"{package_spec.name}={package_spec.version}", channel=channel
    )
    job_id = installer.create([package] + plugins, prefix=prefix)
    return installer._exit_codes[job_id]


def _create_with_plugins_one_by_one(package: str, plugins: List[str], channel: str):
    """Update the package."""
    package_spec = MatchSpec(package)
    prefix = get_prefix_by_name(f"{package_spec.name}-{package_spec.version}")
    installer = CondaInstaller(
        pinned=f"{package_spec.name}={package_spec.version}", channel=channel
    )

    job_id = installer.create([package], prefix=str(prefix))
    for plugin in plugins:
        installer.install([plugin], prefix=str(prefix))

    return installer._exit_codes[job_id]


def check_updates(
    package: str,
    dev: bool = False,
    channel: str = DEFAULT_CHANNEL,
) -> Dict:
    """Check for package updates.

    Parameters
    ----------
    package : str
        The package name to check for new version.
    current_version : str
        The current version of the package.
    dev : bool, optional
        If ``True``, check for development versions. Default is ``False``.
    channel : str, optional
        Check for available versions on this channel. Default is
        ``conda-forge``.

    Returns
    -------
    dict
        Dictionary containing the current and latest versions, found
        installed versions and the installer type used.
    """
    package_spec = MatchSpec(package)
    current_version = str(package_spec.version).rstrip(".*")  # ?
    versions = conda_package_versions(package_spec.name, channel=channel)
    if not dev:
        versions = list(filter(is_stable_version, versions))

    update = False
    latest_version = versions[-1] if versions else ""
    installed_versions_builds = get_installed_versions(package_spec.name)
    # print(installed_versions_builds)
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


def update(
    package,
    plugins=(),
    channel=DEFAULT_CHANNEL,
):
    """Update the package."""
    package_spec = MatchSpec(package)
    plugins = list(plugins)
    return_code = _create_with_plugins(
        package_spec.name, package_spec.version, plugins, channel=channel
    )

    if bool(return_code):
        return_code = _create_with_plugins_one_by_one(package, plugins, channel=channel)

    if not bool(return_code):
        create_sentinel_file(package_spec.name, package_spec.version)
        # TODO: Create a lock file?

    # print("finished!")


def clean_all(package):
    """Clean all environments of a given package.

    Environments will be removed using conda/mamba, or the folders deleted in
    case conda fails.

    Parameters
    ----------
    package_name : str
        Name of the package.
    """
    package_name = MatchSpec(package).name
    # Try to remove using conda/mamba
    installer = CondaInstaller()
    failed = []
    for prefix in get_broken_envs(package_name):
        job_id = installer.remove(prefix)
        if installer._exit_codes[job_id]:
            failed.append(prefix)

    # Otherwise remove the folders manually
    for prefix in failed:
        pass
        # print("removing", prefix)
        # shutil.rmtree(path)


def check_updates_clean_and_launch(
    package: str,
    dev: bool = False,
    channel=DEFAULT_CHANNEL,
):
    """Check for updates and clean."""
    package_spec = MatchSpec(package)
    package_name = package_spec.name
    res = check_updates(package_name, dev, channel)
    found_versions = res["found_versions"]

    # Remove any prior installations
    if res["installed"]:
        for version in found_versions:
            if version != res["latest_version"]:
                remove_sentinel_file(package_name, package_spec.version)

        # Launch the detached application
        # print(f"launching {package_name} version {res['latest_version']}")

        # Remove any prior installations
        clean_all(package_name)


def remove(package: str):
    """Remove specific environment of a given package.

    Environment will be removed using conda/mamba, or the folders deleted in
    case conda fails.

    Parameters
    ----------
    package : str
        Package specification.
    """
    # Try to remove using conda/mamba
    installer = CondaInstaller()
    package_spec = MatchSpec(package)
    prefix = get_prefix_by_name(f"{package_spec.name}-{package_spec.version}")
    job_id = installer.remove(prefix)

    # Otherwise remove the folder manually
    if job_id:
        print("removing", prefix)
        shutil.rmtree(prefix)


def restore(package: str, channel: str = DEFAULT_CHANNEL):
    """Restore specific environment of a given package.

    Parameters
    ----------
    package : str
        Name of the package.
    channel : str, optional
        Check for available versions on this channel. Default is ``conda-forge``
    """
    package_spec = MatchSpec(package)
    package_name = str(package_spec.name)
    current_version = str(package_spec.version).rstrip(".*")  # ?
    env_name = f"{package_name}-{current_version}"
    prefix = str(get_prefix_by_name(env_name))
    installer = CondaInstaller(channel=channel)
    job_id_remove = None
    broken_prefix = ""

    # Remove with conda/mamba
    if os.path.isdir(prefix):
        job_id_remove = installer.remove(prefix)

    # Otherwise rename the folder manually for later deletion
    if job_id_remove and os.path.isdir(prefix):
        broken_prefix = prefix + "-broken"
        os.rename(prefix, broken_prefix)

    # Create restored enviornment
    job_id_restore = installer.create([package], prefix=prefix)

    # Remove the broken folder manually
    if broken_prefix and job_id_remove and os.path.isdir(broken_prefix):
        print("removing", broken_prefix)
        shutil.rmtree(broken_prefix)

    return installer._exit_codes[job_id_restore]
