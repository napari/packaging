"""Constructor manager api."""

from enum import Enum
from typing import List, Optional
import logging

from constructor_manager_api.defaults import DEFAULT_CHANNEL
from constructor_manager_api.utils.worker import ConstructorManagerWorker
from constructor_manager_api.utils.conda import get_prefix_by_name
from constructor_manager_api.utils.settings import save_settings

from qtpy.QtCore import QProcess


logger = logging.getLogger(__name__)


class ActionsEnum(str, Enum):
    check_updates = "check-updates"
    check_version = "check-version"
    check_packages = "check-packages"
    update = "update"
    lock_environment = "lock-environment"
    restore = "restore"
    revert = "revert"
    reset = "reset"
    open = "open"


def _run_action(
    cmd: ActionsEnum,
    package_name: Optional[str] = None,
    version: Optional[str] = None,
    build_string: Optional[str] = None,
    channels: Optional[List[str]] = None,
    dev: bool = False,
    plugins_url: Optional[str] = None,
    target_prefix: Optional[str] = None,
    delayed: bool = False,
    state: Optional[str] = None,
) -> ConstructorManagerWorker:
    """Run constructor action.

    Parameters
    ----------
    cmd : ActionsEnum
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
    target_prefix : str, optional
        Target prefix to install package to, by default ``None``.
    delayed : bool, optional
        Delay execution of action, by default ``False``.
    state : str, optional
        State to restore, by default ``None``.

    Returns
    -------
    ConstructorManagerWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    args = [cmd.value]
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

    if target_prefix:
        args.append("--target-prefix")
        args.append(target_prefix)

    if delayed:
        args.append("--delayed")

    if state:
        args.append("--state")
        args.append(state)

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
    channels: List[str] = [
        DEFAULT_CHANNEL,
    ],
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
        ActionsEnum.check_updates,
        package_name,
        version=current_version,
        build_string=build_string,
        channels=channels,
        dev=dev,
    )


def check_version(package_name: str) -> ConstructorManagerWorker:
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
    return _run_action(ActionsEnum.check_version, package_name)


def check_packages(
    package_name: str,
    version: Optional[str] = None,
    plugins_url: Optional[str] = None,
) -> ConstructorManagerWorker:
    """Check for updates.

    Parameters
    ----------
    package_name : str
        Name of the package to check for updates.
    version : str
        Version of package to execute action on, by default ``None``.

    Returns
    -------
    ConstructorManagerWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action(
        ActionsEnum.check_packages,
        package_name,
        version=version,
        plugins_url=plugins_url,
    )


def update(
    package_name: str,
    current_version: str,
    build_string: Optional[str] = None,
    channels: Optional[List[str]] = None,
    plugins_url: Optional[str] = None,
    dev: bool = False,
    delayed: bool = False,
) -> ConstructorManagerWorker:
    """Update the package to given version.

    If version is None update to latest version found.

    Parameters
    ----------
    package_name : str
        Name of the package to update.
    current_version : str
        Current version of the package to update. This is not the version to
        update to.
    build_string: str, optional
        Build string of the package. For example `'*pyside*`'.
    channels : list of str, optional
        Conda channels to check for updates.
    dev : bool, optional
        Check for development versions of the package, by default ``False``.
    delayed : bool, optional
        Delay execution of action, by default ``False``. Useful when running
        from the main application in the background, instead of using the
        constructor manager UI.

    Returns
    -------
    ConstructorManagerWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action(
        ActionsEnum.update,
        package_name,
        current_version,
        build_string=build_string,
        channels=channels,
        dev=dev,
        delayed=delayed,
        plugins_url=plugins_url,
    )


def restore(
    package_name: str,
    current_version: str,
    state: str,
    channels: Optional[List[str]] = None,
    dev: bool = False,
) -> ConstructorManagerWorker:
    """Restore to a given saved state within the current version.

    Parameters
    ---------
    package_name : str
        Name of the package to check for updates.
    current_version : str, optional
        Version to rollback to, by default ``None``.
    state : str
        State to restore to.
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
        ActionsEnum.restore,
        package_name,
        version=current_version,
        channels=channels,
        dev=dev,
        state=state,
    )


def revert(
    package_name: str,
    current_version: Optional[str],
    channels: Optional[List[str]] = None,
    dev: bool = False,
) -> ConstructorManagerWorker:
    """Revert to a previous version state of the current package.

    Parameters
    ---------
    package_name : str
        Name of the package to check for updates.
    current_version : str, optional
        Current version of the package to revert.
    channels : str, optional
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
        ActionsEnum.revert,
        package_name,
        version=current_version,
        channels=channels,
        dev=dev,
    )


def reset(
    package_name: str,
    current_version: Optional[str],
    channels: Optional[List[str]] = None,
    dev: bool = False,
) -> ConstructorManagerWorker:
    """Reset an environment from scratch.

    This will remove all packages and reinstall the current version
    of the package.

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
        ActionsEnum.reset,
        package_name,
        version=current_version,
        channels=channels,
        dev=dev,
    )


def lock_environment(
    package_name: str,
    current_version: Optional[str],
    plugins_url: Optional[str] = None,
) -> ConstructorManagerWorker:
    """Generate a lock state file using conda-lock for the environment
    with package and version.

    This will generate a state file in the configuration folder, so that
    the restore command can be used with these checkpoints.

    Parameters
    ---------
    package_name : str
        Name of the package to check for updates.
    current_version : str, optional
        Version to rollback to, by default ``None``.
    plugins_url : str, optional
        URL to the plugins to install, by default ``None``.

    Returns
    -------
    ConstructorManagerWorker
        Worker to check for updates. Includes a finished signal that returns
        a ``dict`` with the result.
    """
    return _run_action(
        ActionsEnum.lock_environment,
        package_name,
        version=current_version,
        plugins_url=plugins_url,
    )


def open_manager(
    package_name: str,
    current_version: Optional[str] = None,
    plugins_url: Optional[str] = None,
    build_string: Optional[str] = None,
    channels: Optional[List[str]] = None,
    dev: bool = False,
    log: Optional[str] = None,
) -> bool:
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
    envs = ["_constructor-manager", "constructor-manager", "base"]
    for env in envs:
        target_prefix = get_prefix_by_name(env)
        path = target_prefix / "bin" / "constructor-manager-ui"
        if path.exists():
            break

    settings = {}

    args = [package_name]
    if current_version:
        settings["current_version"] = current_version

    if plugins_url:
        settings["plugins_url"] = plugins_url

    if build_string:
        settings["build_string"] = build_string

    if dev:
        settings["dev"] = dev  # type: ignore

    if channels:
        settings["channels"] = channels  # type: ignore

    if log:
        settings["log"] = log  # type: ignore

    save_settings(package_name, settings)
    # TODO: For a separate PR, use open_application when the convention
    # for applications using constructor nanager is defined in the bundle
    # workflow
    return QProcess.startDetached(
        str(path),
        args,
    )


def open_application(package_name: str, version: str, target_prefix=None):
    """Open the application name for given version in a specific prefix.

    Parameters
    ----------
    package_name : str
        Name of the package to check for updates.
    version : str
        Version to open.
    target_prefix : str, optional
        Target prefix to open the application in, by default ``None``.
    """
    return _run_action(
        ActionsEnum.open,
        package_name,
        version=version,
        target_prefix=target_prefix,
    )
