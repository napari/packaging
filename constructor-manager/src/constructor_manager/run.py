"""Constructor updater api run tester."""

import sys

from qtpy.QtCore import QCoreApplication, QTimer

from constructor_manager.api import check_updates


def _finished(res):
    print("This is the result", res)


if __name__ == "__main__":
    app = QCoreApplication([])

    # Process the event loop
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # type: ignore
    timer.start(100)

    # worker = check_updates("napari", current_version="0.4.15", channel="napari", dev=True)
    worker = check_updates("napari", current_version="0.4.15")
    worker.finished.connect(_finished)
    worker.start()

    sys.exit(app.exec_())
