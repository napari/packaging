"""Version handling utilities."""

import re
from typing import Tuple, Union, TYPE_CHECKING

LETTERS_PATTERN = re.compile(r'[a-zA-Z]')

if TYPE_CHECKING:
    import packaging.version


def is_stable_version(version: Union[Tuple[str], str]) -> bool:
    """Check if a version string corresponds to a stable release.

    Parameters
    ----------
    version : tuple or str
        Version string to check.

    Returns
    -------
    bool
        ``True`` if the version is stable, ``False`` otherwise.

    Examples
    --------
    Stable version examples: ``0.4.12``, ``0.4.1``.
    Non-stable version examples: ``0.4.15beta``, ``0.4.15rc1``, ``0.4.15dev0``.
    """
    if not isinstance(version, tuple):
        version = version.split('.')

    return not LETTERS_PATTERN.search(version[-1])


def parse_version(version : str) -> 'packaging.version._BaseVersion':
    """Parse a version string and return a packaging.version.Version obj.

    Parameters
    ----------
    verstion : str
        Version string to parse.
    """
    import packaging.version

    try:
        return packaging.version.Version(version)
    except packaging.version.InvalidVersion:
        return packaging.version.LegacyVersion(version)
