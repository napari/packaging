import os
import traceback
from pathlib import Path
import platform

from menuinst.api import install, remove, _load
from constructor_manager_cli.utils.conda import get_base_prefix, get_prefix_by_name
from constructor_manager_cli import __version__

TEMPLATE = {
    '$schema': 'https://json-schema.org/draft-07/schema',
    '$id': 'https://schemas.conda.io/menuinst-1.schema.json',
    'menu_name': 'napari (0.4.16)',
    'menu_items': [
    ]
}


# TODO: Use target_prefix
def _locations(package_name, version):
    """Get the location of the shortcut for a package and version."""
    base_prefix = get_base_prefix()
    target_prefix = get_prefix_by_name(f'{package_name}-{version}')
    metadata = _create_shortcut_metadata(package_name, version)
    _, menu_items = _load(metadata, target_prefix, base_prefix)
    locations = [] 
    for menu_item in menu_items:
        locations.append(menu_item.location)

    return locations


def _create_shortcut_metadata(package, version, command=None, description=None, categories=['Development'], icon_path_no_extension=None):
    """Create a shortcut metadata file for menuinst."""
    menu_name = f'{package} ({version})'
    metadata = TEMPLATE.copy()
    metadata['menu_name'] = menu_name
    
    menu_item = {
        'name': menu_name,
        'activate': True,
        'terminal': False,
        'platforms': {
            'win': {
                'desktop': True,
            },
            'linux': {
                'Categories': categories
            },
            'osx': {
                'CFBundleName': package,
                'CFBundleDisplayName': package,
                'CFBundleVersion': version
            }
        }
    }
    if command:
        menu_item['command'] = command

    if description:
        menu_item['description'] = description

    if icon_path_no_extension:
        menu_item['icon'] = str(icon_path_no_extension) + '.{{ ICON_EXT }}'

    metadata['menu_items'] = [menu_item]
    return metadata


def create_temp_shortcut(package, version, command, description= "", categories=['Development'], icon_path_no_extension=None):
    target_prefix = get_prefix_by_name(f'{package}-{version}')
    base_prefix = get_prefix_by_name('base')
    target_prefix = base_prefix
    metadata = _create_shortcut_metadata(
        package=package,
        version=version,
        command=command,
        description=description,
        categories=categories,
        icon_path_no_extension=icon_path_no_extension,
    )
    try:
        paths = install(
            metadata,
            target_prefix=target_prefix,
            base_prefix=base_prefix,
        )
    except FileExistsError as e:        
        # Get the path from the error of the file that already exists
        # TODO: This is only valid for mac
        paths = [Path(e.filename.rsplit('.app/')[0] + '.app')]

    print(paths)
    return paths


def remove_temp_shortcut(package, version, command, description= "", categories=['Development'], icon_path_no_extension=None):
    target_prefix = get_prefix_by_name(f'{package}-{version}')
    base_prefix = get_prefix_by_name('base')

    metadata = _create_shortcut_metadata(
        package=package,
        version=version,
        command=command,
        description=description,
        categories=categories,
        icon_path_no_extension=icon_path_no_extension,
    )

    try:
        paths = remove(
            metadata,
            target_prefix=target_prefix,
            base_prefix=base_prefix,
        )
    except FileExistsError as e:
        pass

    print(paths)
    return paths


def _create_constructor_shortcut(package):
    import constructor_manager_cli.icons

    icon_path_no_extension = Path(constructor_manager_cli.icons.__path__[0]) / 'icon'
    create_temp_shortcut(
        'napari installation manager',
        __version__,
        command=[
            '{{ PYTHON }}',
            '-m',
            'constructor_manager_ui.cli',
            package,
        ],
        icon_path_no_extension=icon_path_no_extension,
        description=f"Manage {package} installations and updates",
        categories=['Development'],
    )


# TODO: Use target_prefix
def open_application(package, version):
    """Open the application using the shortcuts created by menuinst."""
    paths = _locations(package, version)
    if paths:
        path = paths[0]

    plat = platform.system()
    if plat == "Darwin":
        ret_code = os.system(f"open '{path}'")
    elif plat == "Linux":
        cmd = ""
        with open(path) as fh:
            for line in fh:
                if line.startswith("Exec="):
                    cmd = line.split("=", 1)[1].strip()
        if cmd:
            ret_code = os.system(cmd)
    elif plat == "Windows":
        ret_code = os.startfile(path)

    return ret_code
