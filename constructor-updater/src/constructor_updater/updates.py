"""Update utilities."""

import subprocess
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Literal, Tuple, Union
from urllib import request

from constructor_updater.defaults import DEFAULT_CHANNEL
from constructor_updater.utils import _is_stable_version, parse_version
from constructor_updater.packages import pypi_package_versions, pypi_package_data, conda_package_versions


def _get_installed_versions(package_name : str) -> List[str]:
    """Check the current conda prefix for installed versions.

    Parameters
    ----------
        package_name : str
            Name of the package.

    Returns
    -------
    list
        List of installed versions.
    """
    versions = []
    path = Path(sys.prefix)
    envs_folder = path.parent
    # FIXME: what if working from base?
    if envs_folder.parts[-1] == "envs":
        # Check environment name is starts with package_name
        env_paths = [
            env_path
            for env_path in envs_folder.iterdir()
            if env_path.stem.rsplit('-')[0] == package_name
        ]
        for env_path in env_paths:
            conda_meta_folder = envs_folder / env_path / 'conda-meta'
            sentinel_file = conda_meta_folder / f".{package_name}"
            print(env_path)
            if (
                conda_meta_folder.exists()
                and sentinel_file.exists()
                and sentinel_file.is_file()
            ):
                for p in conda_meta_folder.iterdir():
                    if p.suffix == '.json':
                        # Check environment contains a napari package
                        parts = p.stem.rsplit('-')
                        if len(parts) == 3 and parts[-3] == package_name:
                            versions.append(tuple(parts[1:]))
    return versions


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
        versions = list(filter(_is_stable_version, versions))

    update = False
    latest_version = versions[-1] if versions else None
    installed_versions_builds = _get_installed_versions(package_name)
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

def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def update():
    """Update the package."""
    pass
    # Try with all plugins
    # Try with one by one plugins

    # Must print results iteratively 
    # Example
    for path in execute(["locate", "a"]):
        print(path, end="")


package_name = "napari"
current_version = "0.4.16"
# data = conda_package_versions(package_name)
# data = pypi_package_versions(package_name)

# for item in data:
#     print(item, _is_stable_version(item))


print(check_updates(package_name, current_version, stable=False, channel=package_name))
