# Constructor Updater

## Requirements

- packaging
- requests

`conda install python packaging requests -c conda-forge -y`

## Workflow

CLI under progress to be called by a companbion package `constructor-updater-cli`

Currently main function are found in `actions.py`

A constructor installation will contain this package on the `base` environment plus a nother environment
with the application package, for example `napari-0.4.15`

### Check for updates

This will check for updates on package `"napari"` where the current version is `"0.4.15"`, check for `stable`
versions only and using the given conda `channel` (defaults to `"conda-forge"`)

`check_updates("napari", "0.4.15", stable=True, channel="conda-forge")`

### Update

Depending on the result of the previous step, the update procedure can be triggered with:

`update("napari", "0.4.16", "pyside", ["napari-arboretum"])`

where the first argument is the package to update, the second is the new version, the third is any extra
build string and the final argument are the list of plugins to install.

The method will install everything at once (package and pluigns) and if it fails it will install the package
in a new environment named `<package-name>-<version>` and try to install the plugin one by one.

Finally if everything is successful it will add a sentinel file to know the new environment is ready.

### Check updates, launch and clean

Depending on the result of `check_updates`, if the reuslt mentions the new versions is already installed,
then we can run:

`check_updates_clean_and_launch("napari", "0.4.15", stable=True, channel="conda-forge")`

This will check for updates, execute the new version and remove the sentinel files from any other older
environments and delete them

## License

Distributed under the terms of the MIT license. is free and open source software
