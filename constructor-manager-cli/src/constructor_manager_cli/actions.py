"""Constructor manager actions."""
import datetime
import glob
import os
import shutil
import sys
from typing import Dict, List, Optional, Tuple

import yaml
from constructor_manager_cli.defaults import DEFAULT_CHANNEL
from constructor_manager_cli.installer import CondaInstaller
from constructor_manager_cli.utils.anaconda import (
    conda_package_versions,
    plugin_versions,
)
from constructor_manager_cli.utils.conda import (
    get_prefix_by_name,
    parse_conda_version_spec,
)
from constructor_manager_cli.utils.io import (
    create_sentinel_file,
    get_broken_envs,
    get_env_path,
    get_installed_versions,
    get_state_path,
    remove_sentinel_file,
)
from constructor_manager_cli.utils.versions import (
    is_stable_version,
    parse_version,
)


def _create_with_plugins(
    package_name: str,
    version: str,
    build_string: str,
    plugins: List[str] = [],
    channels: Tuple[str] = (DEFAULT_CHANNEL,),
):
    """Update the package.

    Parameters
    ----------
    package : str
        The package name and version spec.
    plugins : list
        List of plugins to install.
    channels : tuple of  str
        The channels to install the package from.

    Returns
    -------
    int
        The return code of the installer.
    """
    # package_name, version = parse_conda_version_spec(package)
    spec = f"{package_name}={version}=*{build_string}*"
    prefix = get_prefix_by_name(f"{package_name}-{version}")
    installer = CondaInstaller(pinned=spec, channels=channels)
    if plugins is not None:
        packages = [spec] + plugins

    job_id = installer.create(packages, prefix=str(prefix))
    return installer._exit_codes[job_id]


def _create_with_plugins_one_by_one(
    package_name: str,
    version: str,
    build_string: str,
    plugins: List[str] = [],
    channels: Tuple[str] = (DEFAULT_CHANNEL,),
):
    """Update the package.

    Parameters
    ----------
    package : str
        The package name and version spec.
    plugins : list
        List of plugins to install.
    channels : tuple of str
        The channels to install the package from.

    Returns
    -------
    int
        The return code of the installer.
    """
    spec = f"{package_name}={version}=*{build_string}*"
    prefix = get_prefix_by_name(f"{package_name}-{version}")
    installer = CondaInstaller(pinned=spec, channels=channels)

    job_id = installer.create([spec], prefix=str(prefix))
    for plugin in plugins:
        installer.install([plugin], prefix=str(prefix))

    return installer._exit_codes[job_id]


def check_updates(
    package: str,
    dev: bool = False,
    channels: Tuple[str] = (DEFAULT_CHANNEL,),
) -> Dict:
    """Check for package updates.

    Parameters
    ----------
    package : str
        The package name to check for new version.
    dev : bool, optional
        If ``True``, check for development versions. Default is ``False``.
    channels : tuple of str, optional
        Check for available versions on these channels. Default is
        ``('conda-forge', )``.

    Returns
    -------
    dict
        Dictionary containing the current and latest versions, found
        installed versions and the installer type used.
    """
    package_name, current_version, build = parse_conda_version_spec(package)
    versions = conda_package_versions(
        package_name, build=build, channels=channels, reverse=True
    )
    if not dev:
        versions = list(filter(is_stable_version, versions))

    update = False
    latest_version = versions[0] if versions else ""
    installed_versions_builds = get_installed_versions(package_name)
    installed_versions = [vb[0] for vb in installed_versions_builds]
    update = parse_version(latest_version) > parse_version(current_version)
    filtered_version = versions[:]
    previous_version: Optional[str] = None
    if current_version in filtered_version:
        index = filtered_version.index(current_version)
        if (index + 1) < len(filtered_version):
            previous_version = filtered_version[index + 1]
        else:
            previous_version = None

    return {
        "available_versions": versions,
        "current_version": current_version,
        "latest_version": latest_version,
        "previous_version": previous_version,
        "found_versions": installed_versions,
        "update": update,
        "installed": latest_version in installed_versions,
        "status": {},
    }


def update(
    package: str,
    dev: bool = False,
    channels: Tuple[str] = (DEFAULT_CHANNEL,),
    plugins: Optional[List[str]] = None,
    plugins_url: Optional[str] = None,
):
    """Update the package.

    Parameters
    ----------
    package : str
        The package name and version spec.
    plugins : list
        List of plugins to install.
    channels : tuple of str
        The channels to install the package from.

    Returns
    -------
    int
        The return code of the installer.
    """
    package_name, current_version, build_string = parse_conda_version_spec(package)
    data = check_updates(package, dev=dev, channels=channels)
    latest_version = data["latest_version"]

    available_plugins = []
    if plugins_url:
        available_plugins = plugin_versions(plugins_url)

    prefix = get_prefix_by_name(f"{package_name}-{current_version}")
    installer = CondaInstaller(channels=channels)
    packages = installer.list(str(prefix))
    info = installer.info(str(prefix))
    platforms = (info.get("platform", ""),)

    # Save state of current environment using conda-lock
    lock_environment(package, channels=channels, platforms=platforms)

    filtered_packages: List[str] = []
    for item in packages:  # type: ignore
        # TODO: Use full spec <name>=<version> ??
        name = item["name"]
        if item["name"] in available_plugins:
            filtered_packages.append(name)

    return_code = _create_with_plugins(
        package_name, latest_version, build_string, filtered_packages, channels=channels
    )

    if bool(return_code):
        # TODO: Erase any folder if it remained?
        return_code = _create_with_plugins_one_by_one(
            package_name,
            latest_version,
            build_string,
            filtered_packages,
            channels=channels,
        )

    if not bool(return_code):
        lock_environment(
            f"{package_name}={latest_version}", channels=channels, platforms=platforms
        )
        create_sentinel_file(package_name, latest_version)


def clean_all(package):
    """Clean all environments of a given package.

    Environments will be removed using conda/mamba, or the folders deleted in
    case conda fails.

    Parameters
    ----------
    package_name : str
        Name of the package.
    """
    package_name, _, _ = parse_conda_version_spec(package)
    installer = CondaInstaller()
    failed = []
    for prefix in get_broken_envs(package_name):
        # Try to remove using conda/mamba
        job_id = installer.remove(prefix)
        if installer._exit_codes[job_id]:
            failed.append(prefix)

    # Otherwise remove the folders manually
    for prefix in failed:
        shutil.rmtree(prefix)


def check_updates_clean_and_launch(
    package: str,
    dev: bool = False,
    channel=DEFAULT_CHANNEL,
):
    """Check for updates and clean."""
    package_name, version, _ = parse_conda_version_spec(package)
    res = check_updates(package_name, dev, channel)
    found_versions = res["found_versions"]

    # Remove any prior installations
    if res["installed"]:
        for version in found_versions:
            if version != res["latest_version"]:
                remove_sentinel_file(package_name, version)

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
    package_name, version, _ = parse_conda_version_spec(package)
    prefix = get_prefix_by_name(f"{package_name}-{version}")
    job_id = installer.remove(prefix)

    # Otherwise remove the folder manually
    if job_id:
        print("removing", prefix)
        shutil.rmtree(prefix)


def restore(package: str, channels: Tuple[str] = (DEFAULT_CHANNEL,)):
    """Restore specific environment of a given package.

    Parameters
    ----------
    package : str
        Name of the package.
    channels : tuple of str, optional
        Check for available versions on these channels.
        Default is ``('conda-forge', )``.
    """
    package_name, current_version, _ = parse_conda_version_spec(package)
    env_name = f"{package_name}-{current_version}"
    prefix = str(get_prefix_by_name(env_name))
    installer = CondaInstaller(channels=channels)
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


def status():
    """ """
    # TODO


def lock_environment(
    package: str,
    channels: Tuple[str] = (DEFAULT_CHANNEL,),
    platforms: Optional[Tuple[str]] = None,
):
    """Lock the environment, using conda lock.

    TODO
    """
    installer = CondaInstaller(channels=channels)
    yaml_spec = {"dependencies": [package]}

    package_name, current_version, _ = parse_conda_version_spec(package)
    prefix = get_prefix_by_name(f"{package_name}-{current_version}")
    if not current_version:
        sys.stderr.write("Cannot lock environment without version number!")
        return 1

    if platforms is None:
        info = installer.info(str(prefix))
        platforms = (info.get("platform", ""),)

    if channels:
        yaml_spec["channels"] = list(channels)

    date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    lockfile = get_state_path() / f"{package_name}-{current_version}-{date}-lock.yaml"

    envs_path = get_env_path()
    envs_path.mkdir(parents=True, exist_ok=True)
    env_path = envs_path / f"{package_name}-{current_version}-environment.yaml"
    with open(env_path, "w") as f:
        yaml.dump(yaml_spec, f)

    installer.lock(
        str(env_path), platforms=platforms, lockfile=str(lockfile), block=True
    )

    with open(lockfile) as fh:
        lines = fh.read().split("\n")

    lines = [line for line in lines if not line.startswith("#")]
    with open(lockfile, "w") as fh:
        data = "\n".join(lines)
        fh.write(data)

    # Check if a file mathcing the lockfile already exists with same content
    filepaths = glob.glob(
        str(get_state_path() / f"{package_name}-{current_version}-*-lock.yaml")
    )
    for filepath in sorted(filepaths, reverse=True):
        with open(filepath) as fh:
            if str(lockfile) != filepath and fh.read() == data:
                lockfile.unlink()
                break

    # return installer._exit_codes[id]
    return "1"
