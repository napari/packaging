"""Constructor manager main interface."""

from typing import Optional
import logging

from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


from constructor_manager_ui.widgets.spinner import SpinnerWidget


logger = logging.getLogger(__name__)


class UpdateWidget(QWidget):

    install_version = Signal(str)
    skip_version = Signal(str)

    def __init__(self, package_name: str, parent: Optional[QWidget] = None):
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
        self.skip_version_button = QPushButton("Skip This Version")
        self.install_version_button = QPushButton("Install This Version")
        self.install_version_button.setObjectName("install_button")
        update_actions_layout.addSpacing(20)
        update_actions_layout.addWidget(new_version_label)
        update_actions_layout.addSpacing(20)
        update_actions_layout.addWidget(self.skip_version_button)
        update_actions_layout.addSpacing(20)
        update_actions_layout.addWidget(self.install_version_button)
        update_actions_layout.addStretch(1)
        new_version_layout.addLayout(update_msg_label_layout)
        new_version_layout.addLayout(update_actions_layout)
        self.skip_version_button.setVisible(False)

        self.update_available_widget.setLayout(new_version_layout)

        # Connect buttons signals to parent class signals
        self.skip_version_button.clicked.connect(
            lambda checked: self.skip_version.emit(self.update_available_version)
        )
        self.install_version_button.clicked.connect(
            lambda checked: self.install_version.emit(self.update_available_version)
        )

    def show_checking_updates_message(self):
        self.update_widgets.setCurrentWidget(self.checking_update_widget)

    def show_up_to_date_message(self):
        self.update_widgets.setCurrentWidget(self.up_to_date_widget)

    def show_update_available_message(self, update_available_version):
        self.update_available_version = update_available_version
        if update_available_version:
            self.update_widgets.setCurrentWidget(self.update_available_widget)
