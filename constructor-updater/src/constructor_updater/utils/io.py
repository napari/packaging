"""IO utilities."""

import sys
from pathlib import Path
from typing import List

from constructor_updater.defaults import (
    SENTINEL_FILE_PREFIX,
    SENTINEL_FILE_SUFFIX,
)
from constructor_updater.utils.conda import normalized_name


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
    path = Path(sys.prefix)
    envs_folder = path.parent
    # FIXME: what if working from base?
    if envs_folder.parts[-1] == "envs":
        # Check environment name is starts with package_name
        env_paths = [
            env_path
            for env_path in envs_folder.iterdir()
            if env_path.stem.rsplit("-")[0] == package_name
        ]
        for env_path in env_paths:
            conda_meta_folder = envs_folder / env_path / "conda-meta"
            sentinel_file = conda_meta_folder / f".{package_name}"
            print(env_path)
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


def sentinel_file_name(package_name):
    """Return the sentinel file name for a package.

    Parameters
    ----------
    package_name : str
        The name of the package to check for a sentinel file.

    Returns
    -------
    str
        The name of the sentinel file.
    """
    package_name = normalized_name(package_name)
    return SENTINEL_FILE_PREFIX + package_name + SENTINEL_FILE_SUFFIX


def create_sentinel_file(package_name, version):
    """"""
    package_name = normalized_name(package_name)
    env_name = f"{package_name}-{version}"
    with open(sentinel_file_name(f"{package_name}-{version}"), "w") as f:
        f.write(version)
