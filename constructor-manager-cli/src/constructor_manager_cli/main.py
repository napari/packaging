"""Command line intrerface to the constructor updater."""

import argparse
import json
import os
import sys
import time
import traceback
from typing import Any, Tuple

from constructor_manager_cli.actions import (
    check_updates,
    lock_environment,
    restore,
    update,
)
from constructor_manager_cli.defaults import DEFAULT_CHANNEL
from constructor_manager_cli.utils.io import get_lock_path
from constructor_manager_cli.utils.locking import FilesystemLock


def _create_subparser(
    subparser,
    channel=False,
    plugins=False,
    dev=False,
    launch=False,
    plugins_url=False,
):
    """Create a subparser for the constructor updater.

    Parameters
    ----------
    subparser : argparse.ArgumentParser
        Subparser to add arguments to.
    channel : bool, optional
        Add channel argument, by default ``False``.
    plugins : bool, optional
        Add plugins argument, by default ``False``.
    dev : bool, optional
        Check for development version, by default ``False``.
    launch : bool, optional
        Launch the aplication, by default ``False``.
    plugins_url : bool, optional
        Add parameter for plugins url providing a json object of plugins
        for the package. By default ``False``.

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

    if plugins:
        subparser.add_argument(
            "--plugins",
            "-p",
            metavar="N",
            type=str,
            nargs="+",
            help="",
            default=[],
        )

    if dev:
        subparser.add_argument("--dev", "-d", action="store_true")

    if launch:
        subparser.add_argument("--launch", "-l", action="store_true")

    if plugins_url:
        subparser.add_argument(
            "--plugins-url",
            "-pu",
            type=str,
        )

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

    # Run the update process (does not delete the previous one)
    update = subparsers.add_parser("update")
    update = _create_subparser(
        update,
        channel=True,
        plugins=True,
        dev=True,
        plugins_url=True,
    )

    # Run the update process after installation, to delete the old envs and
    # optionally launch the application
    update_clean = subparsers.add_parser("update-clean")
    update_clean = _create_subparser(
        update_clean,
        channel=True,
        plugins=True,
        dev=True,
        launch=True,
    )

    # Lock the environemnt using conda-lock
    lock = subparsers.add_parser("lock")
    lock = _create_subparser(lock, channel=True)

    # Restore a current broken version
    restore = subparsers.add_parser("restore")
    restore = _create_subparser(restore, channel=True)

    # Rollback to a previous version
    rollback = subparsers.add_parser("rollback")
    rollback = _create_subparser(rollback, channel=True)

    # Get current status of the installer (update in progress?)
    status = subparsers.add_parser("status")
    status = _create_subparser(status)

    # Clean any broken or stale environments
    clean = subparsers.add_parser("clean")
    clean = _create_subparser(clean)

    clean_lock = subparsers.add_parser("clean-lock")
    clean_lock = _create_subparser(clean_lock)

    return parser


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
    # print(args)
    if args.command == "check-updates":
        res = check_updates(args.package, args.dev, args.channel)
        sys.stdout.write(json.dumps(res, indent=4))
        return

    if args.command == "clean-lock":
        pass

    # Commands that need to be locked
    if lock_created:
        # Then start as usual
        print("RUNNING")
        if args.command == "update":
            res = update(
                args.package,
                args.dev,
                args.channel,
                args.plugins,
                args.plugins_url,
            )
            print(json.dumps(res))
        elif args.command == "update-clean":
            res = check_updates(
                args.package,
                args.dev,
                args.channel,
            )
            print(json.dumps(res))
        elif args.command == "restore":
            res = restore(args.package, args.channel)
            print(json.dumps(res))
        elif args.command == "rollback":
            res = check_updates(
                args.package,
                args.current_version,
                args.stable,
                args.channel,
            )
            print(json.dumps(res))
        elif args.command == "lock":
            res = lock_environment(args.package, args.channel)
            print(json.dumps(res))
        elif args.command == "status":
            pass
        elif args.command == "clean":
            pass

        time.sleep(5)
        lock.unlock()
    else:
        print("ALREADY RUNNING!")


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
    try:
        _execute(args, lock, lock_created)
    except Exception as e:
        try:
            sys.stderr.write(str({"data": {}, "error": json.dumps(e)}))
        except Exception:
            sys.stderr.write(str({"data": {}, "error": traceback.format_exc()}))


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
