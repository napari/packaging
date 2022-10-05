"""IO utilities."""

import os
import sys
from pathlib import Path
from typing import List

from constructor_updater.utils.conda import get_prefix_by_name
from constructor_updater.utils.packages import (
    normalized_name,
    sentinel_file_name,
)


def get_broken_envs(package_name: str) -> List[str]:
    """TODO

    Parameters
    ----------
        package_name : str
            Name of the package.

    Returns
    -------
    list
        List of installed versions.
    """
    broken = []
    envs_folder = get_prefix_by_name("base") / "envs"

    # Check environment name is starts with package_name
    env_paths = [
        env_path
        for env_path in envs_folder.iterdir()
        if env_path.stem.rsplit("-")[0] == package_name and "-" in env_path.stem
    ]
    for env_path in env_paths:
        conda_meta_folder = envs_folder / env_path / "conda-meta"
        sentinel_file = get_sentinel_path(envs_folder / env_path, package_name)
        if (
            conda_meta_folder.exists()
            and not sentinel_file.exists()
            and not sentinel_file.is_file()
        ):
            broken.append(envs_folder / env_path)

    return broken


def get_installed_versions(package_name: str) -> List[str]:
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
    envs_folder = get_prefix_by_name("base") / "envs"

    # Check environment name is starts with package_name
    env_paths = [
        env_path
        for env_path in envs_folder.iterdir()
        if env_path.stem.rsplit("-")[0] == package_name
    ]
    for env_path in env_paths:
        conda_meta_folder = envs_folder / env_path / "conda-meta"
        sentinel_file = get_sentinel_path(envs_folder / env_path, package_name)
        if (
            conda_meta_folder.exists()
            and sentinel_file.exists()
            and sentinel_file.is_file()
        ):
            for p in conda_meta_folder.iterdir():
                if p.suffix == ".json":
                    # Check environment contains a napari package
                    parts = p.stem.rsplit("-")
                    if len(parts) == 3 and parts[-3] == package_name:
                        versions.append(tuple(parts[1:]))
    return versions


def check_if_constructor_app(package_name, path=None) -> bool:
    """"""
    if path is None:
        path = Path(sys.prefix)

    return (path.parent.parent / sentinel_file_name(package_name)).exists()


def get_sentinel_path(prefix, package_name):
    """"""
    return prefix / "conda-meta" / sentinel_file_name(package_name)


def create_sentinel_file(package_name, version):
    """"""
    package_name = normalized_name(package_name)
    env_name = f"{package_name}-{version}"
    prefix = get_prefix_by_name(env_name)
    with open(get_sentinel_path(prefix, package_name), "w") as f:
        f.write("")


def remove_sentinel_file(package_name, version):
    """"""
    package_name = normalized_name(package_name)
    env_name = f"{package_name}-{version}"
    prefix = get_prefix_by_name(env_name)
    os.remove(get_sentinel_path(prefix, package_name))