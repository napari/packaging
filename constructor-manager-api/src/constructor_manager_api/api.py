"""Constructor manager api."""

from typing import List, Optional
import logging

from constructor_manager_api.defaults import DEFAULT_CHANNEL
from constructor_manager_api.utils.worker import ConstructorManagerWorker
from constructor_manager_api.utils.conda import get_base_prefix

from qtpy.QtCore import QProcess


logger = logging.getLogger(__name__)


def _run_action(
    cmd,
    package_name: Optional[str] = None,
    version: Optional[str] = None,
    build_string: Optional[str] = None,
    channels: Optional[List[str]] = None,
    dev: bool = False,
    plugins_url: Optional[str] = None,
) -> ConstructorManagerWorker:
    """Run constructor action.

    Parameters
    ----------
    cmd : str
        Action to run.
    package_name : str, optional
        Name of the package to execute action on.
    version : str, optional
        Version of package to execute action on, by default ``None``.
        If not provided the latest version found will be used.
    channels : list of str, optional
        Channel to check for updates, by default ``[DEFAULT_CHANNEL]``.
    plugins : List[str], optional
        List of plugins to install, by default ``None``.
    dev : bool, optional
        Check for development version, by default ``False``.

    Returns
    -------
    ConstructorManagerWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    args = [cmd]
    if version is None:
        version = "*"

    spec = f"{package_name}={version}"

    if build_string is not None:
        spec += f"=*{build_string}*"

    if package_name is not None and version is not None:
        args.extend([spec])
        if channels:
            for channel in channels:
                args.extend(["--channel", channel])

    if plugins_url:
        args.append("--plugins-url")
        args.append(plugins_url)

    if dev:
        args.extend(["--dev"])

    detached = cmd != "status"
    detached = False

    log_level = logging.getLevelName(logger.getEffectiveLevel())
    args.extend(["--log", log_level])
    logger.debug("Running: constructor-manager %s", " ".join(args))
    return ConstructorManagerWorker(args, detached=detached)


def check_updates(
    package_name: str,
    current_version: Optional[str] = None,
    build_string: Optional[str] = None,
    channels: List[str] = [DEFAULT_CHANNEL, ],
    dev: bool = False,
) -> ConstructorManagerWorker:
    """Check for updates.

    Parameters
    ----------
    package_name : str
        Name of the package to check for updates.
    current_version : str, optional
        Current version of the package. If ``None`` the latest version found
        will be used.
    build_string: str, optional
        Build string of the package.
    channels : list of str, optional
        Channels to check for updates, by default ``[DEFAULT_CHANNEL]``.
    dev : bool, optional
        Check for development version, by default ``False``.

    Returns
    -------
    ConstructorManagerWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action(
        "check-updates",
        package_name,
        version=current_version,
        build_string=build_string,
        channels=channels,
        dev=dev,
    )


def check_version(package_name: str,) -> ConstructorManagerWorker:
    """Check for updates.

    Parameters
    ----------
    package_name : str
        Name of the package to check for updates.

    Returns
    -------
    ConstructorManagerWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action("check-version", package_name)


def check_packages(package_name: str, version: Optional[str] = None, plugins_url: Optional[str] = None) -> ConstructorManagerWorker:
    """Check for updates.

    Parameters
    ----------
    package_name : str
        Name of the package to check for updates.

    Returns
    -------
    ConstructorManagerWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action("check-packages", package_name, version=version, plugins_url=plugins_url)


def update(
    package_name,
    channels: Optional[List[str]] = None,
    dev: bool = False,
) -> ConstructorManagerWorker:
    """Update the package to given version.
    If version is None update to latest version found.

    Returns
    -------
    ConstructorManagerWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action(
        "update", package_name, channels=channels, dev=dev
    )


def restore(
    package_name,
    version,
    channels: Optional[List[str]] = None,
    dev: bool = False,
) -> ConstructorManagerWorker:
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
    ConstructorManagerWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action(
        "restore",
        package_name,
        version=version,
        channels=channels,
        dev=dev,
    )


def revert(
    package_name,
    current_version: Optional[str],
    channels: Optional[List[str]] = None,
    dev: bool = False,
) -> ConstructorManagerWorker:
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
    ConstructorManagerWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action(
        "rollback",
        package_name,
        version=current_version,
        channels=channels,
        dev=dev,
    )


def reset(
    package_name,
    current_version: Optional[str],
    channels: Optional[List[str]] = None,
    dev: bool = False,
) -> ConstructorManagerWorker:
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
    ConstructorManagerWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action(
        "reset",
        package_name,
        version=current_version,
        channels=channels,
        dev=dev,
    )


def get_status():
    """Get status for the state of the constructor updater."""
    return _run_action("status")


def open_manager(
    package_name,
    current_version: Optional[str] = None,
    plugins_url: Optional[str] = None,
    build_string: Optional[str] = None,
    channels: Optional[List[str]] = None,
    dev: bool = False,
    ) -> QProcess:
    """
    Open the constructor manager.

    Parameters
    ----------
    package_name : str
        Name of the package to check for updates.
    current_version : str, optional
        Current version of the package. If ``None`` the latest version found
        will be used.
    build_string: str, optional
        Build string of the package.
    channels : list of str, optional
        Channels to check for updates, by default ``None``.
    dev : bool, optional
        Check for development version, by default ``False``.
    """
    path = (
        get_base_prefix()
        / "bin"
        / "constructor-manager-ui"
    )

    args = [package_name]
    if current_version:
        args.extend(['--current-version', current_version])

    if plugins_url:
        args.extend(['--plugins-url', plugins_url])

    if build_string:
        args.extend(['--build-string', build_string])

    if dev:
        args.extend(['--dev'])

    if channels:
        for channel in channels:
            args.extend(['--channel', channel])

    process = QProcess()
    process.start(
        str(path),
        args
    )
    return process


def open_application(package_name, version):
    return _run_action(
        "open",
        package_name,
        version=version,
    )


def check_constructor_manager_updates():
    # TODO: Use a separate worker and call conda/mamba directly!
    # this could use the same worker and run through constructor-manager-cli
    pass


def update_constructor_manager():
    # Use a separate worker and call conda/mamba directly!
    pass
