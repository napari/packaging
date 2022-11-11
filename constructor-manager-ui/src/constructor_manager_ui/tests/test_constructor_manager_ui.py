"""Tests for the constructor manager UI."""

import pytest


from constructor_manager_ui.main import InstallationManagerDialog


@pytest.fixture
def installation_manager_dlg(qtbot):
    # Mock data for the installation manager dialog
    package_name = "napari"
    install_information = {
        "current_version": {
            "version": "v0.4.16",
            "last_modified": "July 27, 2022",
        },
        "snapshot_version": {
            "version": "v0.4.14",
            "last_modified": "April 5, 2022",
        },
    }
    installation_manager_dlg = InstallationManagerDialog(
        package_name,
        install_information,
    )
    qtbot.addWidget(installation_manager_dlg)
    yield installation_manager_dlg


def test_installation_manager_dialog(installation_manager_dlg):
    update_available_version = "v0.4.17"
    packages = [
        # Package:
        # Name - Version - Source - Build - Plugin
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
    installation_manager_dlg.show()
    installation_manager_dlg.set_packages(packages)
    installation_manager_dlg.show_update_available_message(
        update_available_version
    )
