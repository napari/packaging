"""Command line intrerface to the constructor updater."""

import argparse
import json
import os
import time

from constructor_updater.actions import check_updates
from constructor_updater.defaults import DEFAULT_CHANNEL
from constructor_updater.utils.conda import get_base_prefix
from constructor_updater.utils.locking import FilesystemLock


def create_parser(subparser, channel=False, plugins=False, stable=False):
    """Create a subparser for the constructor updater.

    Parameters
    ----------
    subparser : argparse.ArgumentParser
        Subparser to add arguments to.
    channel : bool, optional
        Add channel argument, by default ``False``.
    plugins : bool, optional
        Add plugins argument, by default ``False``.
    stable : bool, optional
        Add stable argument, by default ``False``.

    Returns
    -------
    argparse.ArgumentParser
        The updated subparser.
    """
    subparser.add_argument("package", type=str)
    subparser.add_argument("--current-version", "-cv", type=str, required=True)

    if channel:
        subparser.add_argument("--channel", "-c", type=str, default=DEFAULT_CHANNEL)

    if plugins:
        subparser.add_argument(
            "--plugins", "-p", metavar="N", type=str, nargs="+", help="", default=[]
        )

    if stable:
        subparser.add_argument("--stable", "-s", action="store_true")

    return subparser


def main():
    """Main function."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        title="subcommands",
        description="valid subcommands",
        help="additional help",
        dest="command",
    )

    check_updates = subparsers.add_parser("check-updates")
    check_updates = create_parser(check_updates, channel=True, stable=True)

    update = subparsers.add_parser("update")
    update = create_parser(update, channel=True, plugins=True, stable=True)

    check_updates_launch_and_clean = subparsers.add_parser("check-launch-clean")
    check_updates_launch_and_clean = create_parser(
        check_updates_launch_and_clean, channel=True, plugins=True, stable=True
    )

    clean = subparsers.add_parser("clean")
    clean = create_parser(clean)

    args = parser.parse_args()
    if args.command is None:
        args = parser.parse_args(["-h"])

    # Try to create lock file
    lock_file = get_base_prefix() / "constructor-updater.lock"
    lock = FilesystemLock(lock_file)
    # Try to lock the lock filelock. If it's *possible* to do it, then
    # there is no previous instance running and we can start a
    # new one. If *not*, then there is an instance already
    # running, which is locking that file
    try:
        lock_created = lock.lock()
    except:
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
        except:
            pass

        handle_excecute(args, lock)
        return None

    handle_excecute(args, lock, lock_created)


def execute(args, lock, lock_created=None):
    """Execute actions.

    args : argparse.Namespace
        Arguments from the command line.
    lock: FilesystemLock
        Lock object.
    lock_created: bool, optional
        Whether the lock was created or not, by default ``None``.
    """
    # Commands that can run in parallel
    print(args)
    if args.command == "check-updates":
        print("RUNNING")
        res = check_updates(
            args.package, args.current_version, args.stable, args.channel
        )
        print(json.dumps(res))
        return

    # Commands that need to be locked
    if lock_created:
        # Then start as usual
        print("RUNNING")
        if args.command == "update":
            res = check_updates(
                args.package, args.current_version, args.stable, args.channel
            )
            print(json.dumps(res))
        elif args.command == "check-clean":
            pass
        elif args.command == "clean":
            pass

        time.sleep(5)
        lock.unlock()
    else:
        print("ALREADY RUNNING!")


def handle_excecute(args, lock, lock_created=None):
    """Execute actions and handle exceptions.

    args : argparse.Namespace
        Arguments from the command line.
    lock: FilesystemLock
        Lock object.
    lock_created: bool, optional
        Whether the lock was created or not, by default ``None``.
    """
    try:
        execute(args, lock, lock_created)
    except Exception as e:
        try:
            print(json.dumps(e))
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
