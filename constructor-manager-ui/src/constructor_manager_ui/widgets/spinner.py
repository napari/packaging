"""Constructor manager main interface."""

from typing import Optional
import logging

from qtpy.QtCore import QSize
from qtpy.QtGui import QMovie
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QWidget,
)


logger = logging.getLogger(__name__)


class SpinnerWidget(QWidget):
    def __init__(self, text: str, parent: Optional[QWidget] = None):
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

    def set_text(self, text: str):
        self.text_label.setText(text)

    def show(self):
        try:
            self.spinner_movie.start()
        except RuntimeError as e:
            pass
        super().show()

    def hide(self):
        try:
            self.spinner_movie.stop()
        except RuntimeError as e:
            pass
        super().hide()
