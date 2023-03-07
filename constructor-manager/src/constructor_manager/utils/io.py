"""IO utilities."""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple, Union

from constructor_manager.utils.conda import get_prefix_by_name
from constructor_manager.utils.packages import (
    normalized_name,
    sentinel_file_name,
)

logger = logging.getLogger(__name__)


def get_broken_envs(package_name: str) -> List[Path]:
    """Find broken conda application environments.

    Parameters
    ----------
    package_name : str
        Name of the package.

    Returns
    -------
    list of Path
        List of installed versions.
    """
    broken = []
    envs_folder = get_prefix_by_name("base") / "envs"

    # Check environment name is starts with package_name
    env_paths = [
        path
        for path in envs_folder.iterdir()
        if path.stem.rsplit("-")[0] == package_name and "-" in path.stem
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


def get_installed_versions(package_name: str) -> List[Tuple[str, ...]]:
    """Check the current conda installation for installed versions in environments.

    Parameters
    ----------
        package_name : str
            Name of the package.

    Returns
    -------
    list of tuples
        List of tuples of installed versions.
    """
    # TODO: Sort by version number
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
                    # Check environment contains the package
                    parts = p.stem.rsplit("-")
                    if len(parts) == 3 and parts[-3] == package_name:
                        versions.append(tuple(parts[1:]))

    return versions


def is_valid_environment(prefix, application_name) -> bool:
    """Check if a given environment is valid."""
    return get_sentinel_path(prefix, application_name).exists()


def get_sentinel_path(prefix: Union[Path, str], package_name: str) -> Path:
    """Sentinel file path for a given environment.

    Parameters
    ----------
    prefix : Path or str
        Path to the environment.
    package_name : str
        Name of the package.

    Returns
    -------
    Path
        Path to the sentinel file.
    """
    prefix = Path(prefix)
    return prefix / "conda-meta" / sentinel_file_name(package_name)


def create_sentinel_file(package_name: str, version: str):
    """Create a sentinel file in the corresponding environment for a given
    package and version.

    Parameters
    ----------
    package_name : str
        Name of the package.
    version : str
        Version of the package.
    """
    package_name = normalized_name(package_name)
    env_name = f"{package_name}-{version}"
    prefix = get_prefix_by_name(env_name)

    with open(get_sentinel_path(prefix, package_name), "w") as f:
        f.write("")


def remove_sentinel_file(package_name: str, version: str):
    """Remove a sentinel file in the corresponding environment for a given
    package and version.

    Parameters
    ----------
    package_name : str
        Name of the package.
    version : str
        Version of the package.
    """
    package_name = normalized_name(package_name)
    env_name = f"{package_name}-{version}"
    prefix = get_prefix_by_name(env_name)
    sentinel_path = get_sentinel_path(prefix, package_name)
    sentinel_path.unlink(True)


@lru_cache
def get_config_path() -> Path:
    # path = get_prefix_by_name("base") / "var" / "constructor-manager"
    path = get_prefix_by_name("constructor-manager") / "var" / "constructor-manager"
    path.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache
def get_state_path() -> Path:
    """Store the output of conda-lock for a given environment."""
    path = get_config_path() / "state"
    path.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache
def get_lock_path() -> Path:
    """Store the lock files."""
    path = get_config_path() / "lock"
    path.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache
def get_log_path() -> Path:
    path = get_config_path() / "log"
    path.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache
def get_status_path() -> Path:
    """Store the output of running conda commands."""
    path = get_config_path() / "status"
    path.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache
def get_env_path() -> Path:
    """Path that stores the input of conda-lock for a given environment.

    The path is created if it does not exist already.
    """
    path = get_config_path() / "env"
    path.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache
def get_list_path() -> Path:
    """Store the output of conda list for a given environment.

    The path is created if it does not exist already.
    """
    path = get_config_path() / "list"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_state_file(
    application: str,
    packages: List[str],
    channels: List[str],
    dev: bool,
    plugins: List[str],
):
    """"""
    base_path = get_state_path()
    base_path.mkdir(parents=True, exist_ok=True)
    data = {
        "application": application,
        "packages": packages,
        "channels": channels,
        "dev": dev,
        "plugins": plugins,
    }
    with open(base_path / f"{application}.json", "w") as f:
        f.write(json.dumps(data, indent=4))


def load_state_file(application: str):
    """"""
    path = get_state_path() / f"{application}.json"
    data = {}
    if path.exists():
        with open(path) as f:
            data = json.loads(f.read())

    return data
