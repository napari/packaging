# Constructor manager

## Requirements

- qtpy
- constructor-manager-cli (on base environment)

## Usage

```python
from constructor_manager.api import check_updates


def finished(result):
    print(result)


worker = check_updates(package_name="napari", current_version="0.4.10", channel="conda-forge")
worker.finished.connect(finished)
worker.start()
```

## License

Distributed under the terms of the MIT license. is free and open source software
