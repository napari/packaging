"""Main interface."""

import sys

from qtpy.QtWidgets import QApplication, QDialog


class Dialog(QDialog):

    def __init__(self):
        super().__init__()
        self.show()


def main(package_name):
    """Run the main interface.

    Parameters
    ----------
    package_name : str
        Name of the package that the installation manager is handling.
    """
    app = QApplication([])
    dialog = Dialog()
    dialog.setWindowTitle(f"{package_name} installation manager")
    sys.exit(app.exec_())
