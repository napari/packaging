"""Command line intrerface to the constructor updater."""

import argparse
import json
import os
import sys
import time
from typing import Any, Tuple

from constructor_manager_cli.actions import ActionManager
from constructor_manager_cli.defaults import DEFAULT_CHANNEL
from constructor_manager_cli.utils.io import get_lock_path
from constructor_manager_cli.utils.locking import FilesystemLock


def _create_subparser(
    subparser,
    channel=False,
    plugins_url=False,
    dev=False,
    launch=False,
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
    launch : bool, optional
        Launch the aplication, by default ``False``.

    Returns
    -------
    argparse.ArgumentParser
        The updated subparser.
    """
    subparser.add_argument("package", type=str)

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

    if launch:
        subparser.add_argument("--launch", "-l", action="store_true")

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

    # Run the update process after installation, to delete the old envs and
    # optionally launch the application
    update_clean = subparsers.add_parser("update-clean")
    update_clean = _create_subparser(
        update_clean,
        channel=True,
        dev=True,
        launch=True,
    )

    # Lock the environment using conda-lock
    lock = subparsers.add_parser("lock")
    lock = _create_subparser(lock, channel=True)

    # Restore to a previous restore point of a current version
    restore = subparsers.add_parser("restore")
    restore = _create_subparser(restore, channel=True)

    # Reset a current broken version to a clean napari install
    reset = subparsers.add_parser("reset")
    reset = _create_subparser(reset, channel=True)

    # Revert to a previous version restore point of a previous version
    revert = subparsers.add_parser("revert")
    revert = _create_subparser(revert, channel=True)

    # Get current status of the installer (update in progress?)
    status = subparsers.add_parser("status")
    status = _create_subparser(status)

    # Clean any broken or stale environments
    clean = subparsers.add_parser("clean")
    clean = _create_subparser(clean)

    clean_lock = subparsers.add_parser("clean-lock")
    clean_lock = _create_subparser(clean_lock)

    return parser


# TODO: Move execute and handle execute to a separate file
# and unify the lock behavior
def _execute(args, lock, lock_created=None):
    """Execute actions.

    Parameters
    ----------
    args : argparse.Namespace
        Arguments from the command line.
    lock: FilesystemLock
        Lock object.
    lock_created: bool, optional
        Whether the lock was created or not, by default ``None``.
    """
    # Commands that can run in parallel
    if "channel" in args:
        manager = ActionManager(args.package, args.channel)
    else:
        manager = ActionManager(args.package)

    if args.command == "check-updates":
        res = manager.check_updates(args.dev)
        sys.stdout.write(json.dumps(res, indent=4))
        return
    elif args.command == "check-version":
        res = manager.check_version()
        sys.stdout.write(json.dumps(res, indent=4))
        return
    elif args.command == "check-packages":
        res = manager.check_packages(args.plugins_url)
        sys.stdout.write(json.dumps(res, indent=4))
        return

    # Commands that need to be locked
    if lock_created:
        if args.command == "update":
            res = manager.update(args.dev, args.plugins_url)
        elif args.command == "update-clean":
            pass
            # res = check_updates(
            #     args.package,
            #     args.dev,
            #     args.channel,
            # )
            # print(json.dumps(res))
        elif args.command == "restore":
            pass
            # res = restore(args.package, args.channel)
            # print(json.dumps(res))
        elif args.command == "rollback":
            pass
            # res = check_updates(
            #     args.package,
            #     args.current_version,
            #     args.stable,
            #     args.channel,
            # )
            # print(json.dumps(res))
        elif args.command == "lock":
            pass
            # res = lock_environment(args.package, args.channel)
            # print(json.dumps(res))
        elif args.command == "status":
            pass
        elif args.command == "clean":
            pass

        time.sleep(5)
        lock.unlock()
    else:
        sys.stdout.write("Another instance is running")


def _handle_excecute(args, lock, lock_created=None):
    """Execute actions and handle exceptions.

    Parameters
    ----------
    args : argparse.Namespace
        Arguments from the command line.
    lock: FilesystemLock
        Lock object.
    lock_created: bool, optional
        Whether the lock was created or not, by default ``None``.
    """
    _execute(args, lock, lock_created)
    # try:
    #     _execute(args, lock, lock_created)
    # except Exception as e:
    #     try:
    #         sys.stderr.write(str({"data": {}, "error": json.dumps(e)}))
    #     except Exception:
    #         sys.stderr.write(str({"data": {}, "error": traceback.format_exc()}))


def _dedup(items: Tuple[Any, ...]) -> Tuple[Any, ...]:
    """Deduplicate an list of items."""
    new_items: Tuple[Any, ...] = ()
    for item in items:
        if item not in new_items:
            new_items += (item,)

    return new_items


def main():
    """Main function."""
    parser = _create_parser()
    args = parser.parse_args()
    if args.command is None:
        args = parser.parse_args(["-h"])

    if "channel" in args:
        args.channel = _dedup(args.channel)

    # Try to create lock file
    constructor_manager_dir = get_lock_path()
    constructor_manager_dir.mkdir(parents=True, exist_ok=True)
    lock_file = constructor_manager_dir / "constructor-manager.lock"

    lock = FilesystemLock(lock_file)
    # Try to lock the lock filelock. If it's *possible* to do it, then
    # there is no previous instance running and we can start a
    # new one. If *not*, then there is an instance already
    # running, which is locking that file
    try:
        lock_created = lock.lock()
    except Exception:
        # If locking fails because of errors in the lockfile
        # module, try to remove a possibly stale lock file.
        try:
            if os.name == "nt":
                if os.path.isdir(lock_file):
                    import shutil

                    shutil.rmtree(lock_file, ignore_errors=True)
            else:
                if os.path.islink(lock_file):
                    os.unlink(lock_file)
        except Exception:
            pass

        _handle_excecute(args, lock)
        return None

    _handle_excecute(args, lock, lock_created)


if __name__ == "__main__":
    main()
