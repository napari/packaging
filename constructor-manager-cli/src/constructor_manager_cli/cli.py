import argparse
import logging

from constructor_manager_cli.defaults import DEFAULT_CHANNEL


logger = logging.getLogger(__name__)


def _create_subparser(
    subparser,
    channel=False,
    plugins_url=False,
    dev=False,
):
    """Create a subparser for the constructor updater.

    Parameters
    ----------
    subparser : argparse.ArgumentParser
        Subparser to add arguments to.
    channel : bool, optional
        Add channel argument, by default ``False``.
    plugins_url : bool, optional
        Add parameter for plugins url providing a json object of plugins
        for the package. By default ``False``.
    dev : bool, optional
        Check for development version, by default ``False``.

    Returns
    -------
    argparse.ArgumentParser
        The updated subparser.
    """
    subparser.add_argument("package", type=str)
    subparser.add_argument(
        "--log",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    if channel:
        subparser.add_argument(
            "--channel",
            "-c",
            action="append",
            default=[DEFAULT_CHANNEL],
        )

    if plugins_url:
        subparser.add_argument(
            "--plugins-url",
            "-pu",
            type=str,
        )

    if dev:
        subparser.add_argument("--dev", "-d", action="store_true")

    return subparser


def _create_parser():
    """Create argument parser and options."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        title="subcommands",
        description="valid subcommands",
        help="additional help",
        dest="command",
    )

    # Check for updates and any current installs
    check_updates = subparsers.add_parser("check-updates")
    check_updates = _create_subparser(
        check_updates,
        channel=True,
        dev=True,
    )

    # Check for current installed version
    check_version = subparsers.add_parser("check-version")
    check_version = _create_subparser(check_version)

    # Check for current installed packages
    check_packages = subparsers.add_parser("check-packages")
    check_packages = _create_subparser(
        check_packages,
        plugins_url=True,
    )

    # Run the update process (does not delete the previous one)
    update = subparsers.add_parser("update")
    update = _create_subparser(
        update,
        channel=True,
        dev=True,
        plugins_url=True,
    )

    # Restore to a previous restore point of a current version
    restore = subparsers.add_parser("restore")
    restore = _create_subparser(restore, channel=True)

    # Revert to a previous version restore point
    revert = subparsers.add_parser("revert")
    revert = _create_subparser(revert, channel=True)

    # Reset to a clean install
    reset = subparsers.add_parser("reset")
    reset = _create_subparser(reset, channel=True)

    # Get current status of the installer (update in progress?)
    status = subparsers.add_parser("status")
    status = _create_subparser(status)

    # Get current status of the installer (update in progress?)
    open = subparsers.add_parser("open")
    open = _create_subparser(open)

    return parser
