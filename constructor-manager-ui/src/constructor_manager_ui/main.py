import logging
import sys
from typing import Any, Tuple

from qtpy.QtWidgets import QApplication

from constructor_manager_ui.style.utils import update_styles
from constructor_manager_ui.widgets.dialog import InstallationManagerDialog
from constructor_manager_ui.cli import create_parser
from constructor_manager_api.utils.settings import load_settings

# To setup image resources for .qss file
from constructor_manager_ui.style import images  # noqa


logger = logging.getLogger(__name__)


def dedup(items: Tuple[Any, ...]) -> Tuple[Any, ...]:
    """Deduplicate an list of items."""
    new_items: Tuple[Any, ...] = ()
    for item in items:
        if item not in new_items:
            new_items += (item,)

    return new_items


def _configure_logging(log_level="WARNING"):
    """Configure logging."""
    import constructor_manager_api

    log_level = getattr(logging, log_level.upper())
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_format = "%(levelname)s - %(message)s"
    logging.basicConfig(format=log_format, level=log_level)

    # Set logging level for libraries used
    api_logger = logging.getLogger(constructor_manager_api.__name__)
    api_logger.setLevel(log_level)


def run():
    """Run the main interface.

    Parameters
    ----------
    package_name : str
        Name of the package that the installation manager is handling.
    """
    parser = create_parser()
    args = parser.parse_args()
    if "channel" in args:
        if args.channel:
            args.channel = dedup(args.channel)

    settings = load_settings(args.package)
    _configure_logging(settings["log"])

    # TODO: Need to add a lock to avoid multiple instances
    app = QApplication([])
    update_styles(app)

    print(args)

    if "current_version" in args:
        current_version = args.current_version or settings["current_version"]

    if "build_string" in args:
        build_string = args.build_string or settings["build_string"]

    if "plugins_url" in args:
        plugins_url = args.plugins_url or settings["plugins_url"]

    if "channel" in args:
        channels = args.channel or dedup(settings["channels"])

    dev = settings["dev"] if settings["dev"] is not None else args.dev
    log = settings["log"] if settings["log"] is not None else args.log

    # Installation manager dialog instance
    installation_manager_dlg = InstallationManagerDialog(
        args.package,
        current_version=current_version,
        build_string=build_string,
        plugins_url=plugins_url,
        channels=channels,
        dev=dev,
        log=log,
    )
    installation_manager_dlg.show()
    sys.exit(app.exec_())
