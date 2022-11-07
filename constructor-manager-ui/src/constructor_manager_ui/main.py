"""Constructor manager main interface."""

from pathlib import Path
import sys

from qtpy.QtCore import QSize, Qt
from qtpy.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

# To setup image resources for .qss file
from .style import images

# UI style constant
QSS_STYLESHEET = Path(__file__).parent / "style" / "base.qss"

# Packages table constants
PLUGINS = 0
ALL_PACKAGES = 1


class PackagesTable(QTableWidget):
    def __init__(self, packages, parent=None):
        super().__init__(parent=parent)
        self.packages = packages
        self.setup()

    def setup(self):
        # Set columns number and headers
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(
            ["Name", "Version", "Source", "Build"]
        )
        self.verticalHeader().setVisible(False)

        # Populate table with data available
        for name, version, source, build, plugin in self.packages:
            self.insertRow(self.rowCount())
            package_row = self.rowCount() - 1
            self.setItem(package_row, 0, QTableWidgetItem(name))
            self.setItem(package_row, 1, QTableWidgetItem(version))
            self.setItem(package_row, 2, QTableWidgetItem(source))
            self.setItem(package_row, 3, QTableWidgetItem(build))

        # Set headers alignment and config
        self.horizontalHeader().setDefaultAlignment(
            Qt.AlignLeft | Qt.AlignVCenter)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Hide table items borders
        self.setShowGrid(False)

    def change_visible_packages(self, toggled_option, checked):
        if checked:
            if toggled_option == PLUGINS:
                for idx, package in enumerate(self.packages):
                    name, version, source, build, plugin = package
                    if not plugin:
                        self.hideRow(idx)
            else:
                for idx, _ in enumerate(self.packages):
                    self.showRow(idx)

    def change_build_column_visibility(self, state):
        if state > Qt.Unchecked:
            self.showColumn(3)
        else:
            self.setColumnHidden(3, True)
            self.horizontalHeader().hideSection(3)
            self.hideColumn(3)


class InstallationManagerDialog(QDialog):

    def __init__(
            self,
            package_name,
            install_information,
            packages,
            update_available_version=None,
            parent=None
    ):
        super().__init__(parent=parent)
        self.package_name = package_name
        self.current_version = install_information['current_version']
        self.snapshot_version = install_information['snapshot_version']
        self.update_available_version = update_available_version
        self.packages = packages
        self.packages_tablewidget = None
        self.setWindowTitle(f"{package_name} installation manager")
        self.setMinimumSize(QSize(500, 500))
        self.setup_layout()
        self.show()

    def _create_install_information_group(self):
        install_information_group = QGroupBox("Install information")
        install_information_layout = QVBoxLayout()
        current_version_layout = QHBoxLayout()

        # Current version labels and button
        current_version_label = QLabel(
            f"{self.package_name} {self.current_version['version']}")
        last_modified_version_label = QLabel(
            f"Last modified {self.current_version['last_modified']}")
        current_version_open_button = QPushButton("Open")
        current_version_open_button.setObjectName("open_button")
        current_version_layout.addWidget(current_version_label)
        current_version_layout.addSpacing(10)
        current_version_layout.addWidget(last_modified_version_label)
        current_version_layout.addSpacing(10)
        current_version_layout.addWidget(current_version_open_button)
        current_version_layout.addStretch(1)
        install_information_layout.addLayout(current_version_layout)

        # Line to divide current section and update section
        install_version_line = QFrame()
        install_version_line.setFrameShape(QFrame.HLine)
        install_version_line.setFrameShadow(QFrame.Sunken)
        install_version_line.setLineWidth(1)
        install_information_layout.addWidget(install_version_line)

        # New version labels and buttons
        new_version_layout = QVBoxLayout()
        if self.update_available_version:
            update_msg_label_layout = QHBoxLayout()
            update_msg_label = QLabel(
                f"A newer version of {self.package_name} is available!")
            update_msg_label_layout.addSpacing(15)
            update_msg_label_layout.addWidget(update_msg_label)

            update_actions_layout = QHBoxLayout()
            new_version_label = QLabel(self.update_available_version)
            skip_version_button = QPushButton("Skip This Version")
            install_version_button = QPushButton("Install This Version")
            install_version_button.setObjectName("install_button")
            update_actions_layout.addSpacing(20)
            update_actions_layout.addWidget(new_version_label)
            update_actions_layout.addSpacing(20)
            update_actions_layout.addWidget(skip_version_button)
            update_actions_layout.addSpacing(20)
            update_actions_layout.addWidget(install_version_button)
            update_actions_layout.addStretch(1)
            new_version_layout.addLayout(update_msg_label_layout)
            new_version_layout.addLayout(update_actions_layout)
        else:
            update_msg_label = QLabel(
                f"Your {self.package_name} is up to date.")
            new_version_layout.addWidget(update_msg_label)
        install_information_group.setLayout(install_information_layout)
        install_information_layout.addLayout(new_version_layout)

        return install_information_group

    def _create_packages_table(self):
        self.packages_tablewidget = PackagesTable(self.packages, parent=self)

        return self.packages_tablewidget

    def _create_packages_group(self):
        packages_group = QGroupBox("Packages")
        packages_layout = QVBoxLayout()

        packages_filter_layout = QHBoxLayout()
        packages_filter_label = QLabel("Show:")
        packages_filter_group = QButtonGroup(self)
        only_plugins_checkbox = QCheckBox("Plugins")
        all_packages_checkbox = QCheckBox("All packages")
        packages_filter_group.addButton(only_plugins_checkbox, PLUGINS)
        packages_filter_group.addButton(all_packages_checkbox, ALL_PACKAGES)
        only_plugins_checkbox.setChecked(True)
        show_build_column_checkbox = QCheckBox("Build")
        show_build_column_checkbox.setChecked(True)

        packages_filter_layout.addWidget(packages_filter_label)
        packages_filter_layout.addWidget(only_plugins_checkbox)
        packages_filter_layout.addWidget(all_packages_checkbox)
        packages_filter_layout.addWidget(show_build_column_checkbox)
        packages_filter_layout.addStretch(1)

        packages_tablewidget = self._create_packages_table()
        packages_layout.addLayout(packages_filter_layout)
        packages_layout.addWidget(packages_tablewidget)
        packages_group.setLayout(packages_layout)

        packages_filter_group.idToggled.connect(
            packages_tablewidget.change_visible_packages)
        show_build_column_checkbox.stateChanged.connect(
            packages_tablewidget.change_build_column_visibility)
        packages_tablewidget.change_visible_packages(PLUGINS, True)
        packages_tablewidget.change_build_column_visibility(
            show_build_column_checkbox.checkState())

        return packages_group

    def _create_installation_actions_group(self):
        installation_actions_group = QGroupBox("Installation Actions")

        revert_action_layout = QHBoxLayout()
        revert_button = QPushButton("Revert Installation")
        revert_label = QLabel(
            "Rollback installation to the latest snapshot: "
            f"{self.snapshot_version['version']} "
            f"({self.snapshot_version['last_modified']})"
        )
        revert_action_layout.addWidget(revert_button)
        revert_action_layout.addSpacing(10)
        revert_action_layout.addWidget(revert_label)
        revert_action_layout.addStretch(1)

        reset_action_layout = QHBoxLayout()
        reset_button = QPushButton("Reset installation")
        reset_label = QLabel(
            "Reset the installation to clear "
            "preferences, plugins, and other packages"
        )
        reset_action_layout.addWidget(reset_button)
        reset_action_layout.addSpacing(10)
        reset_action_layout.addWidget(reset_label)
        reset_action_layout.addStretch(1)

        uninstall_action_layout = QHBoxLayout()
        uninstall_button = QPushButton("Uninstall")
        uninstall_button.setObjectName("uninstall_button")
        uninstall_label = QLabel(
            "Remove the {self.package_name} Bundled App"
            "and Installation Manager from your computer"
        )
        uninstall_action_layout.addWidget(uninstall_button)
        uninstall_action_layout.addSpacing(10)
        uninstall_action_layout.addWidget(uninstall_label)
        uninstall_action_layout.addStretch(1)

        installation_actions_layout = QVBoxLayout()
        installation_actions_layout.addLayout(revert_action_layout)
        installation_actions_layout.addLayout(reset_action_layout)
        installation_actions_layout.addLayout(uninstall_action_layout)
        installation_actions_group.setLayout(installation_actions_layout)

        return installation_actions_group

    def setup_layout(self):
        main_layout = QVBoxLayout(self)

        # Install information
        install_information_group = self._create_install_information_group()
        main_layout.addWidget(install_information_group)

        # Packages
        packages_group = self._create_packages_group()
        main_layout.addWidget(packages_group)

        # Installation Actions
        installation_actions_group = self._create_installation_actions_group()
        main_layout.addWidget(installation_actions_group)

        # Layout
        self.setLayout(main_layout)


def main(package_name):
    """Run the main interface.

    Parameters
    ----------
    package_name : str
        Name of the package that the installation manager is handling.
    """
    app = QApplication([])
    app.setStyleSheet(open(QSS_STYLESHEET, "r").read())
    # Mock data for the installation manager dialog
    install_information = {
        "current_version": {
            "version": "v0.4.16",
            "last_modified": "July 27, 2022"
        },
        "snapshot_version": {
            "version": "v0.4.14",
            "last_modified": "April 5, 2022"
        }
    }
    update_available_version = "v0.4.17"
    packages = [
        # Package:
        # Name - Version - Source - Build - Plugin
        ("napari-console", "0.1.6", "pip", None, True),
        ("napari-live-recording", "0.1.6rc", "conda/conda-forge",
         "pyhd3eb1b0_0", True),
        ("napari-microscope", "0.7", "pip", None, True),
        ("alabaster", "0.7.12", "conda/conda-forge", "pyhd3eb1b0_0", False),
        ("aom", "3.5.0", "conda/conda-forge", "pyhd3eb1b0_0", False),
        ("appdirs", "1.4.4", "conda/conda-forge", "pyhd3eb1b0_0", False),
        ("appnope", "0.1.2", "conda/conda-forge", "pyhd3eb1b0_0", False),
    ]

    # Installation manager dialog instance
    installation_manager_dlg = InstallationManagerDialog(
        package_name,
        install_information,
        packages,
        update_available_version=update_available_version)
    sys.exit(app.exec_())
