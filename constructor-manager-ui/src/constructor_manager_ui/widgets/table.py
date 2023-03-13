"""Constructor manager main interface."""

import logging

from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush
from qtpy.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


# Packages table constants
RELATED_PACKAGES = 0
ALL_PACKAGES = 1


logger = logging.getLogger(__name__)


class PackagesTable(QTableWidget):
    def __init__(self, packages, visible_packages=RELATED_PACKAGES, parent=None):
        super().__init__(parent=parent)
        self.packages = packages
        self.visible_packages = visible_packages
        self.setup()

    def _create_item(self, text: str, related_package: bool):
        item = QTableWidgetItem(text)
        if related_package:
            background_brush = QBrush(Qt.GlobalColor.black)
        else:
            background_brush = QBrush(Qt.GlobalColor.darkGray)

        item.setBackground(background_brush)
        if not related_package:
            foreground_brush = QBrush(Qt.GlobalColor.black)
            item.setForeground(foreground_brush)

        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item

    def setup(self):
        # Set columns number and headers
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["Name", "Version", "Source", "Build"])
        self.verticalHeader().setVisible(False)

        # Set horizontal headers alignment and config
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Hide table items borders
        self.setShowGrid(False)

        # Set table selection to row
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

    def set_data(self, packages):
        self.clearContents()
        self.setRowCount(0)
        self.packages = packages

        # Populate table with data available
        for name, version, source, build, related_package in self.packages:
            self.insertRow(self.rowCount())
            package_row = self.rowCount() - 1
            self.setItem(package_row, 0, self._create_item(name, related_package))
            self.setItem(package_row, 1, self._create_item(version, related_package))
            self.setItem(package_row, 2, self._create_item(source, related_package))
            self.setItem(package_row, 3, self._create_item(build, related_package))
            if self.visible_packages == RELATED_PACKAGES and not related_package:
                self.hideRow(package_row)

    def change_visible_packages(self, toggled_option):
        if self.packages:
            self.visible_packages = toggled_option
            if toggled_option == RELATED_PACKAGES:
                for idx, package in enumerate(self.packages):
                    name, version, source, build, related_package = package
                    if not related_package:
                        self.hideRow(idx)
            else:
                for idx, _ in enumerate(self.packages):
                    self.showRow(idx)
        else:
            self.visible_packages = toggled_option

    def change_detailed_info_visibility(self, state):
        if state > Qt.Unchecked:
            self.showColumn(2)
            self.showColumn(3)
            self.change_visible_packages(ALL_PACKAGES)
        else:
            self.hideColumn(2)
            self.hideColumn(3)
            self.change_visible_packages(RELATED_PACKAGES)
