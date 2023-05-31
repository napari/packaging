"""Defaults and constants."""

DEFAULT_CHANNEL = "conda-forge"
SENTINEL_FILE_PREFIX = "."
SENTINEL_FILE_SUFFIX = "_is_bundled_constructor"
# TODO: Add timeout for requests and timeout for subprocesses
DEFAULT_TIMEOUT = 60  # Seconds
DEFAULT_REQUEST_TIMEOUT = 60  # Seconds
DEFAULT_PROCESS_TIMEOUT = 60 * 60  # Seconds
DEFAULT_MENU_TEMPLATE = "{package_name}-{version}-menu"
