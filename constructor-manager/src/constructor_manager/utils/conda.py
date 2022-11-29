"""Conda utilities."""

import sys
from pathlib import Path


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
