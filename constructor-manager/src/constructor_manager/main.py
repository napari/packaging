"""Command line intrerface to the constructor updater."""

import json
import logging
import sys
import traceback
import warnings

from constructor_manager.actions import ActionManager
from constructor_manager.cli import _create_parser
from constructor_manager.defaults import DEFAULT_CHANNEL
from constructor_manager.utils.io import get_lock_path
from constructor_manager.utils.locking import get_lock
from constructor_manager.utils.misc import dedup


warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


_COMMANDS = {
    "check-updates": ["dev"],
    "check-version": [],
    "check-packages": ["plugins_url"],
    "status": [],
    "open": ["target_prefix"],
}
_COMMANDS_LOCKED = {
    "update": ["plugins_url", "dev", "delayed"],
    "restore": [],
    "revert": [],
    "reset": [],
    "uninstall": [],
    "lock-environment": ["plugins_url"],
}


def _execute(args, lock_file_path):
    """Execute actions.

    Parameters
    ----------
    arguments : argparse.Namespace
        Arguments from the command line.
    lock_file_path : str
        Path to the lock file.
    """
    channels = (DEFAULT_CHANNEL,) if "channel" not in args else args.channel
    manager = ActionManager(args.application, channels)

    all_commands = {**_COMMANDS, **_COMMANDS_LOCKED}
    method_name = args.command.lower().replace("-", "_")
    method = getattr(manager, method_name)
    method_kwargs = {
        arg_name: getattr(args, arg_name) for arg_name in all_commands[args.command]
    }

    lock, lock_created = get_lock(lock_file_path)
    if lock_created:
        lock.unlock()

    method_kwargs["lock_created"] = lock_created
    result = []
    if args.command in _COMMANDS:
        result = method(**method_kwargs)
        # time.sleep(5)
    elif args.command in _COMMANDS_LOCKED:
        logger.debug("Creating lock file: %s", lock_file_path)
        lock, lock_created = get_lock(lock_file_path)
        if lock_created:
            result = method(**method_kwargs)
            # time.sleep(5)
            lock.unlock()
        else:
            result = "Another instance is running"

    return result


def _configure_logging(log_level: str = "WARNING"):
    """Configure logging.

    Parameters
    ----------
    log_level : str, optional
        Log level, by default ``"WARNING"``.
    """
    log_level = getattr(logging, log_level.upper(), logging.WARNING)  # type: ignore
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=log_format, level=log_level)


def main():
    """Main function."""
    parser = _create_parser()
    args = parser.parse_args()
    if getattr(args, "command", None) is None:
        parser.print_help()
        return

    if getattr(args, "log", None):
        _configure_logging(args.log)

    # Deduplicate channels
    if "channel" in args:
        args.channel = dedup(args.channel)

    # Get lockfile path
    constructor_manager_dir = get_lock_path()
    constructor_manager_dir.mkdir(parents=True, exist_ok=True)
    lock_file_path = constructor_manager_dir / "constructor-manager.lock"

    # result = _execute(args, lock_file_path)
    try:
        logger.debug("Executing: %s", args)
        result = _execute(args, lock_file_path)
        sys.stdout.write(str(json.dumps({"data": result, "error": ""}, indent=4)))
    except Exception as error:
        try:
            data = {"data": {}, "error": error}
            sys.stdout.write(json.dumps(data, indent=4))
            sys.stderr.write(error)
        except Exception:
            data = {"data": {}, "error": traceback.format_exc()}
            sys.stdout.write(json.dumps(data, indent=4))
