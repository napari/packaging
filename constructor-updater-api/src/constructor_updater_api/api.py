"""Constructor updater api actions."""

from constructor_updater_api.defaults import DEFAULT_CHANNEL
from constructor_updater_api.utils.worker import ContructorUpdaterWorker


def check_updates(package_name, current_version, channel: str=DEFAULT_CHANNEL, dev:bool = False) -> ContructorUpdaterWorker:
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
    args = ["check-updates", f'{package_name}={current_version}', "--channel", channel]
    if dev:
        args.extend(["--dev"])

    return ContructorUpdaterWorker(args)
