"""Constructor manager main interface."""

from pathlib import Path
import sys

from qtpy.QtCore import QSize, Qt, QTimer, Signal
from qtpy.QtGui import QMovie
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
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# To setup image resources for .qss file
from constructor_manager_ui.style import images
# To get mock data
from constructor_manager_ui.data import (
    INSTALL_INFORMATION,
    UPDATE_AVAILABLE_VERSION,
    PACKAGES
)

# UI style constant
QSS_STYLESHEET = Path(__file__).parent / "style" / "base.qss"

# Packages table constants
PLUGINS = 0
ALL_PACKAGES = 1


class SpinnerWidget(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent=parent)
        # Widgets for text and loading gif
        self.text_label = QLabel(text)
        spinner_label = QLabel()
        self.spinner_movie = QMovie(":/images/loading.gif")
        self.spinner_movie.setScaledSize(QSize(18, 18))
        spinner_label.setMovie(self.spinner_movie)

        # Set layout for text + loading indicator
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text_label)
        layout.addWidget(spinner_label)
        layout.addStretch(1)
        self.setLayout(layout)
        self.spinner_movie.start()

    def set_text(self, text):
        self.text_label.setText(text)

    def show(self):
        self.spinner_movie.start()
        super().show()

    def hide(self):
        self.spinner_movie.stop()
        super().hide()


class UpdateWidget(QWidget):

    install_version = Signal(str)
    skip_version = Signal(str)

    def __init__(self, package_name, parent=None):
        super().__init__(parent=parent)
        self.package_name = package_name
        self.update_available_version = None

        # Setup widgets
        self.checking_update_widget = SpinnerWidget(
            "Checking for updates...", parent=self
        )
        self.up_to_date_widget = QWidget(self)
        self._initialize_up_to_date_widget()
        self.update_available_widget = QWidget(self)
        self._initialize_update_available_widget()

        # Stack widgets to show one at a time and set layout
        update_widget_layout = QHBoxLayout()
        self.update_widgets = QStackedWidget(self)
        self.update_widgets.addWidget(self.checking_update_widget)
        self.update_widgets.addWidget(self.up_to_date_widget)
        self.update_widgets.addWidget(self.update_available_widget)
        update_widget_layout.addWidget(self.update_widgets)
        self.setLayout(update_widget_layout)

        # Start showing checking updates widget
        self.show_checking_updates_message()

    def _initialize_up_to_date_widget(self):
        up_to_date_layout = QVBoxLayout()
        update_msg_label = QLabel(f"Your {self.package_name} is up to date.")
        up_to_date_layout.addWidget(update_msg_label)

        self.up_to_date_widget.setLayout(up_to_date_layout)

    def _initialize_update_available_widget(self):
        new_version_layout = QVBoxLayout()
        update_msg_label_layout = QHBoxLayout()
        update_msg_label = QLabel(
            f"A newer version of {self.package_name} is available!"
        )
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

        self.update_available_widget.setLayout(new_version_layout)

        # Connect buttons signals to parent class signals
        skip_version_button.clicked.connect(
            lambda checked: self.skip_version.emit(
                self.update_available_version
            )
        )
        install_version_button.clicked.connect(
            lambda checked: self.install_version.emit(
                self.update_available_version
            )
        )

    def show_checking_updates_message(self):
        self.update_widgets.setCurrentWidget(self.checking_update_widget)

    def show_up_to_date_message(self):
        self.update_widgets.setCurrentWidget(self.up_to_date_widget)

    def show_update_available_message(self, update_available_version):
        self.update_available_version = update_available_version
        if update_available_version:
            self.update_widgets.setCurrentWidget(self.update_available_widget)


class PackagesTable(QTableWidget):
    def __init__(self, packages, visible_packages=PLUGINS, parent=None):
        super().__init__(parent=parent)
        self.packages = packages
        self.visible_packages = visible_packages
        self.setup()

    def setup(self):
        # Set columns number and headers
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["Name", "Version", "Source", "Build"])
        self.verticalHeader().setVisible(False)

        # Set headers alignment and config
        self.horizontalHeader().setDefaultAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Hide table items borders
        self.setShowGrid(False)

    def set_data(self, packages):
        self.packages = packages

        # Populate table with data available
        for name, version, source, build, plugin in self.packages:
            self.insertRow(self.rowCount())
            package_row = self.rowCount() - 1
            self.setItem(package_row, 0, QTableWidgetItem(name))
            self.setItem(package_row, 1, QTableWidgetItem(version))
            self.setItem(package_row, 2, QTableWidgetItem(source))
            self.setItem(package_row, 3, QTableWidgetItem(build))
            if self.visible_packages == PLUGINS and not plugin:
                self.hideRow(package_row)

    def change_visible_packages(self, toggled_option, checked):
        if checked and self.packages:
            self.visible_packages = toggled_option
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
        parent=None,
    ):
        super().__init__(parent=parent)
        self.package_name = package_name
        self.current_version = install_information["current_version"]
        self.snapshot_version = install_information["snapshot_version"]
        self.updates_widget = None
        self.packages_tablewidget = None
        self.setWindowTitle(f"{package_name} installation manager")
        self.setMinimumSize(QSize(500, 500))
        self.setup_layout()

    def _create_install_information_group(self):
        install_information_group = QGroupBox("Install information")
        install_information_layout = QVBoxLayout()
        current_version_layout = QHBoxLayout()

        # Current version labels and button
        current_version_label = QLabel(
            f"{self.package_name} {self.current_version['version']}"
        )
        last_modified_version_label = QLabel(
            f"Last modified {self.current_version['last_modified']}"
        )
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
        install_version_line.setObjectName("separator")
        install_version_line.setFrameShape(QFrame.HLine)
        install_version_line.setFrameShadow(QFrame.Sunken)
        install_version_line.setLineWidth(1)
        install_information_layout.addWidget(install_version_line)

        # Update information widget
        self.updates_widget = UpdateWidget(self.package_name, parent=self)
        install_information_layout.addWidget(self.updates_widget)
        install_information_group.setLayout(install_information_layout)

        # Signals
        # Open button signal
        current_version_open_button.clicked.connect(self.open_installed)
        # Update widget signals
        self.updates_widget.install_version.connect(self.install_version)
        self.updates_widget.skip_version.connect(self.skip_version)

        return install_information_group

    def _create_packages_group(self):
        packages_group = QGroupBox("Packages")
        packages_layout = QVBoxLayout()

        packages_filter_layout = QHBoxLayout()
        packages_filter_label = QLabel("Show:")
        packages_filter_group = QButtonGroup(self)
        only_plugins_checkbox = QCheckBox("Plugins")
        all_packages_checkbox = QCheckBox("All packages")
        self.packages_spinner_label = SpinnerWidget(
            "Loading packages...", parent=self
        )
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
        packages_filter_layout.addWidget(self.packages_spinner_label)

        self.packages_tablewidget = PackagesTable(None, parent=self)
        packages_layout.addLayout(packages_filter_layout)
        packages_layout.addWidget(self.packages_tablewidget)
        packages_group.setLayout(packages_layout)

        packages_filter_group.idToggled.connect(
            self.packages_tablewidget.change_visible_packages
        )
        show_build_column_checkbox.stateChanged.connect(
            self.packages_tablewidget.change_build_column_visibility
        )
        self.packages_tablewidget.change_visible_packages(PLUGINS, True)
        self.packages_tablewidget.change_build_column_visibility(
            show_build_column_checkbox.checkState()
        )

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
            f"Remove the {self.package_name} Bundled App "
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

        revert_button.clicked.connect(self.revert_installation)
        reset_button.clicked.connect(self.reset_installation)
        uninstall_button.clicked.connect(self.uninstall)

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

    def open_installed(self):
        # TODO: To be handled with the backend.
        #       Maybe this needs to be a signal
        print(self.current_version)

    def show_checking_updates_message(self):
        self.updates_widget.show_checking_updates_message()

    def show_up_to_date_message(self):
        self.updates_widget.show_up_to_date_message()

    def show_update_available_message(self, update_available_version):
        self.updates_widget.show_update_available_message(
            update_available_version
        )

    def install_version(self, update_version):
        # TODO: To be handled with the backend.
        #       Maybe this needs to be a signal
        print(update_version)

    def skip_version(self, skip_version):
        # TODO: To be handled with the backend.
        #       Maybe this needs to be a signal
        print(skip_version)

    def set_packages(self, packages):
        self.packages_spinner_label.show()
        self.packages = packages
        if self.packages_tablewidget:
            self.packages_tablewidget.set_data(self.packages)
            self.packages_spinner_label.hide()

    def revert_installation(self):
        # TODO: To be handled with the backend.
        #       Maybe this needs to be a signal
        print("Revert installation")

    def reset_installation(self):
        # TODO: To be handled with the backend.
        #       Maybe this needs to be a signal
        print("Reset installation")

    def uninstall(self):
        # TODO: To be handled with the backend.
        #       Maybe this needs to be a signal
        print("Uninstall")


def main(package_name):
    """Run the main interface.

    Parameters
    ----------
    package_name : str
        Name of the package that the installation manager is handling.
    """
    app = QApplication([])
    app.setStyleSheet(open(QSS_STYLESHEET, "r").read())

    # Installation manager dialog instance
    installation_manager_dlg = InstallationManagerDialog(
        package_name,
        INSTALL_INFORMATION,
    )
    installation_manager_dlg.show()

    # Mock data initialization loading.
    # Change commented lines to check different UI update widget states
    def data_initialization():
        installation_manager_dlg.set_packages(PACKAGES)
        installation_manager_dlg.show_update_available_message(
            UPDATE_AVAILABLE_VERSION
        )
        # installation_manager_dlg.show_up_to_date_message()

    QTimer.singleShot(5000, data_initialization)

    sys.exit(app.exec_())
