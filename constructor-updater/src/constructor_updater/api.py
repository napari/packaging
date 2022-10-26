"""Constructor updater api."""

from typing import List, Optional

from constructor_updater.defaults import DEFAULT_CHANNEL
from constructor_updater.utils.worker import ConstructorUpdaterWorker


def _run_action(
    cmd,
    package_name: Optional[str] = None,
    version: Optional[str] = None,
    channel: str = DEFAULT_CHANNEL,
    plugins: Optional[List[str]] = None,
    dev: bool = False,
) -> ConstructorUpdaterWorker:
    """Run constructor action.

    Parameters
    ----------
    cmd : str
        Action to run.
    package_name : str, optional
        Name of the package to execute action on.
    version : str, optional
        Version of package to execute action on, by default ``None``.
    channel : str, optional
        Channel to check for updates, by default ``DEFAULT_CHANNEL``.
    plugins : List[str], optional
        List of plugins to install, by default ``None``.
    dev : bool, optional
        Check for development version, by default ``False``.

    Returns
    -------
    ContructorUpdaterWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    args = [cmd]
    if package_name is not None and version is not None:
        spec: Optional[str] = f"{package_name}={version}"
    else:
        spec = package_name

    if package_name is not None and version is not None:
        args.extend([spec, "--channel", channel])

    if plugins:
        args.append("--plugins")
        args.extend(plugins)

    if dev:
        args.extend(["--dev"])

    detached = cmd != "status"
    return ConstructorUpdaterWorker(args, detached=detached)


def check_updates(
    package_name, current_version, channel: str = DEFAULT_CHANNEL, dev: bool = False
) -> ConstructorUpdaterWorker:
    """Check for updates.

    Parameters
    ----------
    package_name : str
        Name of the package to check for updates.
    current_version : str
        Current version of the package.
    channel : str, optional
        Channel to check for updates, by default ``DEFAULT_CHANNEL``.
    dev : bool, optional
        Check for development version, by default ``False``.

    Returns
    -------
    ContructorUpdaterWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action(
        "check-updates", package_name, version=current_version, channel=channel, dev=dev
    )


def update(
    package_name,
    channel: str = DEFAULT_CHANNEL,
    plugins: Optional[List[str]] = None,
    dev: bool = False,
) -> ConstructorUpdaterWorker:
    """Update the package to given version.
    If version is None update to latest version found.

    Returns
    -------
    ContructorUpdaterWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action(
        "update", package_name, channel=channel, plugins=plugins, dev=dev
    )


def rollback(
    package_name,
    current_version: Optional[str],
    channel: str = DEFAULT_CHANNEL,
    plugins: Optional[List[str]] = None,
    dev: bool = False,
) -> ConstructorUpdaterWorker:
    """Update the package to given version.
    If version is None update to latest version found.

    Parameters
    ---------
    package_name : str
        Name of the package to check for updates.
    version : str, optional
        Version to rollback to, by default ``None``.
    channel : str, optional
        Channel to check for updates, by default ``DEFAULT_CHANNEL``.
    dev : bool, optional
        Check for development version, by default ``False``.

    Returns
    -------
    ContructorUpdaterWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action(
        "rollback",
        package_name,
        version=current_version,
        channel=channel,
        plugins=plugins,
        dev=dev,
    )


def restore(
    package_name,
    version,
    channel: str = DEFAULT_CHANNEL,
    dev: bool = False,
    plugins: Optional[List[str]] = None,
) -> ConstructorUpdaterWorker:
    """Restore the current version of package.

    Parameters
    ---------
    package_name : str
        Name of the package to check for updates.
    version : str, optional
        Version to rollback to, by default ``None``.
    channel : str, optional
        Channel to check for updates, by default ``DEFAULT_CHANNEL``.
    dev : bool, optional
        Check for development versions, by default ``False``.

    Returns
    -------
    ContructorUpdaterWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action(
        "restore",
        package_name,
        version=version,
        channel=channel,
        plugins=plugins,
        dev=dev,
    )


def status():
    """Get status for the state of the constructor updater."""
    return _run_action("status")
