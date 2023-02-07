import logging
import sys
from typing import Any, Tuple


from qtpy.QtWidgets import QApplication

# TODO: MOVE SOMEWHERE ELSE, do not use CLI directly
from constructor_manager_ui.style.utils import update_styles
from constructor_manager_ui.widgets import InstallationManagerDialog
from constructor_manager_ui.cli import create_parser


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
    import constructor_manager

    log_level = getattr(logging, log_level.upper())
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_format = "%(levelname)s - %(message)s"
    logging.basicConfig(format=log_format, level=log_level)

    # Set logging level for libraries used
    api_logger = logging.getLogger(constructor_manager.__name__)
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
    _configure_logging(args.log)

    # TODO: Need to add a lock to avoid multiple instances!
    app = QApplication([])
    update_styles(app)

    if "channel" in args:
        if args.channel:
            args.channel = dedup(args.channel)

    # Installation manager dialog instance
    installation_manager_dlg = InstallationManagerDialog(
        args.package,
        args.current_version,
        plugins_url=args.plugins_url,
        build_string=args.build_string,
        channels=args.channel,
        dev=args.dev,
    )
    installation_manager_dlg.show()
    sys.exit(app.exec_())


# TODO:
# - Add settings to the installation manager
# - read from settings and CLI, CLI has priority
