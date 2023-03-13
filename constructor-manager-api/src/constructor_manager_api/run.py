"""Constructor updater api run tester."""

import sys

from qtpy.QtCore import QCoreApplication, QTimer  # type: ignore

from constructor_manager_api.api import open_manager


def _finished(res):
    print("This is the result", res)


if __name__ == "__main__":
    app = QCoreApplication([])

    # Process the event loop
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # type: ignore
    timer.start(100)

    # worker = check_updates(
    #     "napari",
    #     current_version="0.4.15",
    #     channel="napari",
    #     dev=True,
    # )
    # worker = check_updates(
    #     "napari",
    #     build_string="pyside",
    #     plugins_url="https://api.napari-hub.org/plugins",
    # )
    # worker = check_version("napari")
    # worker.finished.connect(_finished)
    # worker.start()

    process = open_manager(
        "napari",
        build_string="pyside",
        plugins_url="https://api.napari-hub.org/plugins",
        channels=["napari", "conda-forge"],
        log="DEBUG",
    )
    sys.exit(process)
    # sys.exit(app.exec_())
