"""Tests for the constructor manager UI."""

import pytest

from constructor_manager_ui.data import (
    INSTALL_INFORMATION,
    PACKAGE_NAME,
    PACKAGES,
    UPDATE_AVAILABLE_VERSION,
)
from constructor_manager_ui.main import InstallationManagerDialog


@pytest.fixture
def installation_manager_dlg(qtbot):
    # Initialize installation manager with mock data
    installation_manager_dlg = InstallationManagerDialog(
        PACKAGE_NAME,
        INSTALL_INFORMATION,
    )
    qtbot.addWidget(installation_manager_dlg)
    yield installation_manager_dlg


def test_installation_manager_dialog(installation_manager_dlg):
    installation_manager_dlg.show()
    installation_manager_dlg.set_packages(PACKAGES)
    installation_manager_dlg.show_update_available_message(UPDATE_AVAILABLE_VERSION)
