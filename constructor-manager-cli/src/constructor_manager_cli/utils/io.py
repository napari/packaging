"""IO utilities."""

import json
import os
import sys
from pathlib import Path
from typing import List, Tuple

from constructor_manager_cli.utils.conda import get_prefix_by_name
from constructor_manager_cli.utils.packages import (
    normalized_name,
    sentinel_file_name,
)


def get_broken_envs(package_name: str) -> List[Path]:
    """TODO

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
    """Check the current conda prefix for installed versions.

    Parameters
    ----------
        package_name : str
            Name of the package.

    Returns
    -------
    list of tuples
        List of tuples of installed versions.
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


def get_config_path() -> Path:
    return get_prefix_by_name("base") / "constructor-manager"


def get_state_path() -> Path:
    return get_config_path() / "state"


def get_lock_path() -> Path:
    return get_config_path() / "lock"


def get_log_path() -> Path:
    return get_config_path() / "log"


def get_status_path() -> Path:
    return get_config_path() / "status"


def save_state_file(application, packages, channel, dev, plugins):
    """"""
    base_path = get_state_path()
    base_path.mkdir(parents=True, exist_ok=True)
    data = {
        "application": application,
        "packages": packages,
        "channel": channel,
        "dev": dev,
        "plugins": plugins,
    }
    with open(base_path / f"{application}.json", "w") as f:
        f.write(json.dumps(data, indent=4))


def load_state_file(application):
    """"""
    path = get_state_path() / f"{application}.json"
    data = {}
    if path.exists():
        with open(path) as f:
            data = json.loads(f.read())

    return data
