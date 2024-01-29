"""Mock data for the installation manager dialog UI."""

from typing import Dict, Optional, List, NamedTuple

# Types
VersionInfo = Dict[str, str]


class PackageData(NamedTuple):
    name: str
    version: str
    source: str
    build: Optional[str]
    plugin: bool


PACKAGE_NAME: str = "napari"
INSTALL_INFORMATION: Dict[str, VersionInfo] = {
    "current_version": {
        "version": "v0.4.16",
        "last_modified": "July 27, 2022",
    },
    "snapshot_version": {
        "version": "v0.4.14",
        "last_modified": "April 5, 2022",
    },
}
UPDATE_AVAILABLE_VERSION: str = "v0.4.17"
PACKAGES: List[PackageData] = [
    # Package:
    # Name - Version - Source - Build - Related package (plugin or package itself)
    PackageData("napari", "0.4.16", "pip", None, True),
    PackageData("napari-console", "0.1.6", "pip", None, True),
    PackageData(
        "napari-live-recording",
        "0.1.6rc",
        "conda/conda-forge",
        "pyhd3eb1b0_0",
        True,
    ),
    PackageData("napari-microscope", "0.7", "pip", None, True),
    PackageData("alabaster", "0.7.12", "conda/conda-forge", "pyhd3eb1b0_0", False),
    PackageData("aom", "3.5.0", "conda/conda-forge", "pyhd3eb1b0_0", False),
    PackageData("appdirs", "1.4.4", "conda/conda-forge", "pyhd3eb1b0_0", False),
    PackageData("appnope", "0.1.2", "conda/conda-forge", "pyhd3eb1b0_0", False),
]
