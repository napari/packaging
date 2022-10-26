# Constructor Updater Commnand line interface

## Requirements

- packaging
- requests

`conda install python packaging requests -c conda-forge -y`

## Workflow

CLI under progress to be called by a companbion package `constructor-updater-cli`

Currently main function are found in `actions.py`

A constructor installation will contain this package on the `base` environment plus a nother environment
with the application package, for example `napari-0.4.15`
