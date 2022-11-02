"""Conda utilities."""

import sys
from pathlib import Path
from typing import List, Optional, Tuple, Union

from conda.models.match_spec import MatchSpec  # type: ignore
from constructor_manager_cli.utils.packages import sentinel_file_name


def parse_conda_version_spec(package: str) -> Tuple[str, str]:
    """Parse a conda version spec into a tuple of (name, version).

    Parameters
    ----------
    package : str
        The package name and version spec.

    Returns
    -------
    tuple
        The package name and version.
    """
    package_spec = MatchSpec(package)
    version = str(package_spec.version).rstrip(".*")  # ?
    return package_spec.name, version


def check_if_constructor_app(package_name, path=None) -> bool:
    """FIXME:"""
    if path is None:
        path = Path(sys.prefix)

    return (path.parent.parent / sentinel_file_name(package_name)).exists()


def check_if_conda_environment(
    path: Union[Optional[Path], Optional[str]] = None
) -> bool:
    """Check if path is a conda environment.

    Parameters
    ----------
    path : str, optional
        If `None` then check if current process is running in a conda
        environment.

    Returns
    -------
    bool
    """
    if path is None:
        path = Path(sys.prefix)

    return (Path(path) / "conda-meta" / "history").exists()


def get_base_prefix() -> Path:
    """Get base conda prefix.

    Returns
    -------
    pathlib.Path
        Base conda prefix.
    """
    current = Path(sys.prefix)
    if (current / "envs").exists() and (current / "envs").is_dir():
        return current

    if current.parent.name == "envs" and current.parent.is_dir():
        return current.parent.parent

    return current


def get_prefix_by_name(name: Optional[str] = None) -> Path:
    """Get conda prefix by environment name.

    This does not check if the environment exists.

    Parameters
    ----------
    name : str, optional
        Name of the environment. If `None` then return the current prefix.

    Returns
    -------
    pathlib.Path
        Conda prefix for the corresponding ``name``.
    """
    base_prefix = get_base_prefix()
    if name is None:
        return Path(sys.prefix)
    elif name == "base":
        return base_prefix
    else:
        return base_prefix / "envs" / name


def list_packages(prefix: str, plugins: Optional[List] = None):
    """List packages in a conda environment.

    Optionally filter by plugin list.

    Parameters
    ----------
    prefix : str
        The conda environment prefix.
    plugins : list, optional
        List of plugins to filter by.

    Returns
    -------
    list
        List of packages in the environment.
    """
    packages = []
    for path in (Path(prefix) / "conda-meta").iterdir():
        if path.is_file() and path.name.endswith(".json"):
            parts = path.name.rsplit("-")
            b, v, name = parts[-1], parts[-2], "-".join(parts[:-2])
            b = b.replace(".json", "")
            packages.append((name, v, b))

    if plugins is not None:
        packages = [pkg for pkg in packages if pkg[0] in plugins]

    return packages
