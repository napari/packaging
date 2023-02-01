"""Command line intrerface to the constructor updater."""

import logging
import json
import sys
import traceback
import warnings

from constructor_manager_cli.actions import ActionManager
from constructor_manager_cli.defaults import DEFAULT_CHANNEL
from constructor_manager_cli.utils.io import get_lock_path
from constructor_manager_cli.utils.locking import get_lock
from constructor_manager_cli.utils.misc import dedup
from constructor_manager_cli.cli import _create_parser


warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


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
    channels = (DEFAULT_CHANNEL,) if "channel" not in args else args.channel
    manager = ActionManager(args.package, channels)

    # Commands that can run in parallel
    result = []
    if args.command == "check-updates":
        result = manager.check_updates(args.dev)
    elif args.command == "check-version":
        result = manager.check_version()
    elif args.command == "check-packages":
        result = manager.check_packages(args.plugins_url)

    if result:
        return result

    # Commands that need to be locked
    if lock_created:
        if args.command == "update":
            result = manager.update(args.dev, args.plugins_url)
        elif args.command == "restore":
            result = manager.restore()
        elif args.command == "revert":
            result = manager.revert()
        elif args.command == "reset":
            result = manager.reset()
        elif args.command == "status":
            result = manager.get_status()

        # time.sleep(5)
        lock.unlock()
        return result
    else:
        return "Another instance is running"


def _configure_logging(log_level="WARNING"):
    """Configure logging."""
    log_level = getattr(logging, log_level.upper())
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=log_format, level=log_level)


def main():
    """Main function."""
    parser = _create_parser()
    args = parser.parse_args()
    _configure_logging(args.log)

    if args.command is None:
        args = parser.parse_args(["-h"])

    if "channel" in args:
        args.channel = dedup(args.channel)

    # Try to create lock file
    constructor_manager_dir = get_lock_path()
    constructor_manager_dir.mkdir(parents=True, exist_ok=True)
    lock_file_path = constructor_manager_dir / "constructor-manager.lock"

    logger.debug("Creating lock file: %s", lock_file_path)
    lock, lock_created = get_lock(lock_file_path)
    result = {}
    try:
        logger.debug("Executing: %s", args)
        result = _execute(args, lock, lock_created)
        sys.stdout.write(str(json.dumps({"data": result, "error": ""}, indent=4)))
    except Exception as error:
        try:
            data = {"data": result, "error": error}
            sys.stdout.write(json.dumps(data, indent=4))
            sys.stderr.write(error)
        except Exception:
            sys.stderr.write(str({"data": {}, "error": traceback.format_exc()}))


if __name__ == "__main__":
    main()
