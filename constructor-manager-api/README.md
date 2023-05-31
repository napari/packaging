# Constructor manager API

## Requirements

- qtpy
- constructor-manager-cli (on base environment)

## Usage

```python
from constructor_manager_api.api import check_updates


def finished(result):
    print(result)


worker = check_updates(package_name="napari", current_version="0.4.10", channels=[]"conda-forge"])
worker.finished.connect(finished)
worker.start()
```

## Other examples

```python
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

    worker = check_updates(
        "napari",
        current_version="0.4.15",
        channel="napari",
        dev=True,
    )
    worker = check_updates(
        "napari",
        build_string="pyside",
        plugins_url="https://api.napari-hub.org/plugins",
    )
    worker = check_version("napari")
    worker.finished.connect(_finished)
    worker.start()
    sys.exit(app.exec_())
```

## License

Distributed under the terms of the MIT license. is free and open source software
