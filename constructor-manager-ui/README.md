# Constructor Manager User Interface

## Requirements

- qtpy
- (pyqt/pyside2)

## Development

Install for development with PyQt5:

```bash
pip install -e .[pyqt5]
```

Install for development with PySide2:

```bash
pip install -e .[pyside2]
```

Install testing dependencies:

```bash
pip install -e .[testing]
```

Install typing dependencies:

```bash
pip install -e .[typing]
```

Run the application:

```bash
constructor-manager-ui napari
```

Generate resources file:

Once installed, run the command below to generate the resource file:

```bash
constructor-manager-ui-qrc
```

You need to have pyqt5 installed.

### Example commands

```bash
constructor-manager-ui napari --current-version 0.4.16 --build-string pyside --plugins-url https://api.napari-hub.org/plugins --channel conda-forge --channel napari
constructor-manager-ui napari --build-string pyside --plugins-url https://api.napari-hub.org/plugins --channel conda-forge --channel napari
constructor-manager-ui napari --build-string pyside --plugins-url https://api.napari-hub.org/plugins --channel conda-forge --channel napari --dev
constructor-manager-ui napari --build-string pyside --plugins-url https://api.napari-hub.org/plugins --channel conda-forge --channel napari -cv 0.4.17
```
