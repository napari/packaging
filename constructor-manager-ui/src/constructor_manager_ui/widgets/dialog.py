"""Constructor manager main dialog."""

from typing import Optional, List
import logging

from qtpy.QtCore import QProcess, QSize, QTimer, Qt
from qtpy.QtGui import QCloseEvent
from qtpy.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QMessageBox,
)

from constructor_manager_api import (
    check_updates,
    check_version,
    check_packages,
    restore,
    revert,
    reset,
    open_application,
    update,
)

# To get mock data
from constructor_manager_ui.data import PackageData
from constructor_manager_ui.widgets.spinner import SpinnerWidget
from constructor_manager_ui.widgets.table import PackagesTable
from constructor_manager_ui.widgets.update import UpdateWidget

# Packages table constants
RELATED_PACKAGES = 0
ALL_PACKAGES = 1


logger = logging.getLogger(__name__)


class InstallationManagerDialog(QDialog):
    def __init__(
        self,
        package_name: str,
        current_version: Optional[str] = None,
        build_string: Optional[str] = None,
        plugins_url: Optional[str] = None,
        channels: Optional[List[str]] = None,
        dev: bool = False,
        log: str = "WARNING",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent)
        self.package_name = package_name
        self.current_version = current_version
        self.plugins_url = plugins_url
        self.build_string = build_string
        self.channels = channels
        self.dev = dev
        self.log = log
        self._busy = False
        self.snapshot_version = None
        self.updates_widget = None
        self.packages_tablewidget = None
        self._worker_version = None

        # Setup
        self.setWindowTitle(f"{package_name} installation manager")
        self.setMinimumSize(QSize(500, 750))
        self.setup_layout()
        self._refresh()

    def _create_install_information_group(self):
        install_information_group = QGroupBox("Install information")
        install_information_layout = QVBoxLayout()
        current_version_layout = QHBoxLayout()

        # Current version labels and button
        if self.current_version:
            text = f"{self.package_name} v{self.current_version}"
        else:
            text = self.package_name

        self.current_version_label = QLabel(text)
        last_modified_version_label = QLabel()
        # f"Last modified {self.current_version['last_modified']}"
        # )
        self.current_version_open_button = QPushButton("Open")
        self.current_version_open_button.setObjectName("open_button")
        self.refresh_button = QPushButton("Refresh")
        current_version_layout.addWidget(self.current_version_label)
        current_version_layout.addSpacing(10)
        current_version_layout.addWidget(last_modified_version_label)
        current_version_layout.addSpacing(10)
        current_version_layout.addWidget(self.current_version_open_button)
        current_version_layout.addStretch(1)
        current_version_layout.addWidget(self.refresh_button)
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
        self.current_version_open_button.clicked.connect(self.open_installed)

        # Update widget signals
        self.updates_widget.install_version.connect(self.install_version)
        self.updates_widget.skip_version.connect(self.skip_version)
        self.refresh_button.clicked.connect(self._refresh)
        self.refresh_button.setVisible(False)

        return install_information_group

    def _create_packages_group(self):
        packages_group = QGroupBox("Packages")
        packages_layout = QVBoxLayout()

        packages_filter_layout = QHBoxLayout()
        packages_filter_label = QLabel("Show:")
        self.packages_spinner_label = SpinnerWidget("Loading packages...", parent=self)
        show_detailed_view_checkbox = QCheckBox("Detailed view")
        show_detailed_view_checkbox.setChecked(False)

        packages_filter_layout.addWidget(packages_filter_label)
        packages_filter_layout.addWidget(show_detailed_view_checkbox)
        packages_filter_layout.addStretch(1)
        packages_filter_layout.addWidget(self.packages_spinner_label)

        self.packages_tablewidget = PackagesTable(None, parent=self)
        packages_layout.addLayout(packages_filter_layout)
        packages_layout.addWidget(self.packages_tablewidget)
        packages_group.setLayout(packages_layout)

        show_detailed_view_checkbox.stateChanged.connect(
            self.packages_tablewidget.change_detailed_info_visibility
        )
        self.packages_tablewidget.change_detailed_info_visibility(
            show_detailed_view_checkbox.checkState()
        )

        return packages_group

    def _create_installation_actions_group(self):
        installation_actions_group = QGroupBox("Installation Actions")
        installation_actions_layout = QGridLayout()

        self.spinner_installation_actions = SpinnerWidget("", parent=self)
        self.spinner_installation_actions.setVisible(False)
        installation_actions_layout.addWidget(QLabel(""), 0, 0)
        installation_actions_layout.addWidget(
            self.spinner_installation_actions, 0, 1, alignment=Qt.AlignRight
        )

        # Restore action
        self._restore_button = QPushButton("Restore Installation")
        self.restore_label = QLabel(
            "Restore installation to the latest snapshot of the current version: "
            # f"{self.snapshot_version['version']} "
            # f"({self.snapshot_version['last_modified']})"
        )
        installation_actions_layout.addWidget(self._restore_button, 1, 0)
        installation_actions_layout.addWidget(self.restore_label, 1, 1)

        # Revert action
        self._revert_button = QPushButton("Revert Installation")
        self.revert_label = QLabel(
            "Rollback installation to the latest snapshot of the previous version: "
            # f"{self.snapshot_version['version']} "
            # f"({self.snapshot_version['last_modified']})"
        )
        installation_actions_layout.addWidget(self._revert_button, 2, 0)
        installation_actions_layout.addWidget(self.revert_label, 2, 1)

        # Reset action
        self._reset_button = QPushButton("Reset Installation")
        self.reset_label = QLabel(
            "Reset the current installation to clear "
            "preferences, plugins, and other packages"
        )
        installation_actions_layout.addWidget(self._reset_button, 3, 0)
        installation_actions_layout.addWidget(self.reset_label, 3, 1)

        # Uninstall action
        self.uninstall_button = QPushButton("Uninstall")
        self.uninstall_button.setObjectName("uninstall_button")
        self.uninstall_label = QLabel(
            f"Remove the {self.package_name} Bundled App "
            "and Installation Manager from your computer"
        )
        self.uninstall_button.setVisible(False)
        self.uninstall_label.setVisible(False)
        # TODO: to be enabled later on
        # installation_actions_layout.addWidget(self.uninstall_button, 3, 0)
        # installation_actions_layout.addWidget(uninstall_label, 3, 1)

        installation_actions_group.setLayout(installation_actions_layout)

        # Signals
        self._restore_button.clicked.connect(self.restore_installation)
        self._revert_button.clicked.connect(self.revert_installation)
        self._reset_button.clicked.connect(self.reset_installation)
        self.uninstall_button.clicked.connect(self.uninstall)

        return installation_actions_group

    def _create_feedback_group(self):
        feedback_group = QGroupBox("Feedback")
        self._status_data = QTextEdit(self)
        self._status_error = QTextEdit(self)

        self._status_data.setReadOnly(True)
        self._status_error.setReadOnly(True)

        feedback_layout = QVBoxLayout()
        feedback_status_layout = QHBoxLayout()
        feedback_status_layout.addWidget(self._status_data)
        feedback_status_layout.addWidget(self._status_error)

        feedback_layout.addLayout(feedback_status_layout)
        feedback_group.setLayout(feedback_layout)
        return feedback_group

    def setup_layout(self):
        main_layout = QVBoxLayout(self)

        # Install information
        install_information_group = self._create_install_information_group()
        main_layout.addWidget(install_information_group, stretch=2)

        # Packages
        packages_group = self._create_packages_group()
        main_layout.addWidget(packages_group, stretch=2)

        # Installation Actions
        installation_actions_group = self._create_installation_actions_group()
        main_layout.addWidget(installation_actions_group, stretch=2)

        # Installation Actions
        feedback_group = self._create_feedback_group()
        main_layout.addWidget(feedback_group, stretch=1)
        print(self.log)
        feedback_group.setVisible(self.log == "DEBUG")

        # Layout
        self.setLayout(main_layout)

        self.set_version_actions_enabled(False)

    def _refresh(self):
        self.set_busy(True)
        self.refresh_button.setVisible(False)
        self.packages_spinner_label.show()
        self._worker_version = check_version(self.package_name)
        self._worker_version.finished.connect(self._update_version)
        self._worker_version.start()
        self.show_checking_updates_message()

    def _refresh_after_version(self):
        self._worker_packages = check_packages(
            self.package_name,
            version=self.current_version,
            plugins_url=self.plugins_url,
        )
        self._worker_packages.finished.connect(self._update_packages)
        self._worker_packages.start()

        self._worker_updates = check_updates(
            self.package_name,
            current_version=self.current_version,
            build_string=self.build_string,
            channels=self.channels,
            dev=self.dev,
        )
        self._worker_updates.finished.connect(self._update_widget)
        self._worker_updates.start()

        self.show_checking_updates_message()

    def _update_version(self, result):
        self._handle_finished(result)
        if result.get("exit_code") == 0:
            data = result["data"]
            self.current_version = data.get("version", "")

            if self.current_version:
                text = f"v{self.current_version}"
            else:
                text = "(Not installed!)"

            self.current_version_open_button.setEnabled(bool(self.current_version))

            self.current_version_label.setText(f"{self.package_name} {text}")
            self.current_version_open_button.setVisible(True)

        self._refresh_after_version()

    def _update_packages(self, result):
        self._handle_finished(result)
        data = result["data"]
        package_data = []
        if isinstance(data, dict):
            packages = data.get("packages", [])
            for pkg in packages:
                package_data.append(
                    PackageData(
                        pkg["name"],
                        pkg["version"],
                        pkg["source"],
                        pkg["build_string"],
                        pkg["is_plugin"],
                    )
                )

        self.set_packages(package_data)
        self.set_busy(False)
        self.refresh_button.setVisible(True)

    def _update_widget(self, result):
        self._handle_finished(result)
        if result.get("exit_code") == 0:
            data = result["data"]
            if data.get("update"):
                self.show_update_available_message(data.get("latest_version"))
            else:
                self.show_up_to_date_message()

            states = data.get("states", [])
            if states:
                print(states)

    # Qt Overrides
    def closeEvent(self, event: QCloseEvent) -> None:
        """Override Qt method."""
        if self._busy:
            QMessageBox.warning(
                self, "Busy", "Please wait until the current action finishes!"
            )
            event.ignore()
            return

        # while ConstructorManagerWorker._WORKERS:
        #     worker = ConstructorManagerWorker._WORKERS.pop()
        #     self._terminate_worker(worker)

        return super().closeEvent(event)

    # Helpers
    def _handle_finished(self, result):
        self._status_data.append("<br>")
        self._status_error.append("<br>")
        data = result.get("data", {})
        error = result.get("error", "")
        self._status_data.append(str(data))
        self._status_error.append(str(error))

    def _terminate_worker(self, worker):
        not_running = QProcess.ProcessState.NotRunning
        if worker and worker.state() != not_running:
            self._worker_version.terminate()

    def handle_finished(self, result):
        self._handle_finished(result)
        self.spinner_installation_actions.hide()
        self._refresh()

    def show_checking_updates_message(self):
        self.updates_widget.show_checking_updates_message()

    def show_up_to_date_message(self):
        self.updates_widget.show_up_to_date_message()

    def show_update_available_message(self, update_available_version):
        self.updates_widget.show_update_available_message(update_available_version)

    def set_packages(self, packages):
        self.packages = packages
        if self.packages_tablewidget:
            self.packages_tablewidget.set_data(self.packages)
            self.packages_spinner_label.hide()

    def set_busy(self, value):
        self._restore_button.setDisabled(value)
        self._revert_button.setDisabled(value)
        self._reset_button.setDisabled(value)
        self._busy = value

    def set_version_actions_enabled(self, value):
        self._restore_button.setEnabled(value)
        self._revert_button.setEnabled(value)
        self._reset_button.setEnabled(value)
        self.current_version_open_button.setVisible(value)

    # Actions
    def open_installed(self):
        self._open_worker = open_application(self.package_name, self.current_version)
        self._open_worker.start()
        self.current_version_open_button.setEnabled(False)

        # Disable open button for a bit
        self._timer_open_button = QTimer()
        self._timer_open_button.timeout.connect(
            lambda: self.current_version_open_button.setEnabled(True)
        )
        self._timer_open_button.setSingleShot(True)
        self._timer_open_button.start(10000)

    def install_version(self, update_version):
        print("Update version")
        worker = update(
            self.package_name,
            self.current_version,
            build_string=self.build_string,
            channels=self.channels,
            plugins_url=self.plugins_url,
            dev=self.dev,
            delayed=False,
        )
        worker.finished.connect(self.handle_finished)
        worker.start()
        self.set_busy(True)

    def restore_installation(self):
        self.spinner_installation_actions.set_text("Restoring installation...")
        self.spinner_installation_actions.show()
        worker = restore(self.package_name)
        worker.finished.connect(self.handle_finished)
        worker.start()
        self.set_busy(True)

    def revert_installation(self):
        self.spinner_installation_actions.set_text("Reverting installation...")
        self.spinner_installation_actions.show()
        worker = revert(self.package_name, self.current_version)
        worker.finished.connect(self.handle_finished)
        worker.start()
        self.set_busy(True)

    def reset_installation(self):
        self.spinner_installation_actions.set_text("Reseting installation...")
        self.spinner_installation_actions.show()
        self._worker = reset(
            package_name=self.package_name,
            current_version=self.current_version,
            channels=self.channels,
        )
        self._worker.finished.connect(self.handle_finished)
        self._worker.start()
        self.set_busy(True)

    def skip_version(self, skip_version):
        pass

    def uninstall(self):
        pass
