"""Mock data for the installation manager dialog UI."""

PACKAGE_NAME = "napari"
INSTALL_INFORMATION = {
    "current_version": {
        "version": "v0.4.16",
        "last_modified": "July 27, 2022",
    },
    "snapshot_version": {
        "version": "v0.4.14",
        "last_modified": "April 5, 2022",
    },
}
UPDATE_AVAILABLE_VERSION = "v0.4.17"
PACKAGES = [
    # Package:
    # Name - Version - Source - Build - Related package (plugin or package itself)
    ("napari", "0.4.16", "pip", None, True),
    ("napari-console", "0.1.6", "pip", None, True),
    (
        "napari-live-recording",
        "0.1.6rc",
        "conda/conda-forge",
        "pyhd3eb1b0_0",
        True,
    ),
    ("napari-microscope", "0.7", "pip", None, True),
    ("alabaster", "0.7.12", "conda/conda-forge", "pyhd3eb1b0_0", False),
    ("aom", "3.5.0", "conda/conda-forge", "pyhd3eb1b0_0", False),
    ("appdirs", "1.4.4", "conda/conda-forge", "pyhd3eb1b0_0", False),
    ("appnope", "0.1.2", "conda/conda-forge", "pyhd3eb1b0_0", False),
]
