"""Utility functions to update and load the application style."""

from pathlib import Path
from typing import Dict
from subprocess import check_call

from qtpy.QtWidgets import QApplication  # type: ignore

# UI style constant
CWD = Path(__file__).parent
STYLE_VARIABLES = CWD / "style_variables.txt"
QSS_STYLESHEET = CWD / "base.qss"
IMAGES = CWD / "images"
IMAGES_QRC = CWD / "images.qrc"
IMAGES_PY = CWD / "images.py"


def _load_styles(stylesheet_file, style_variables: Dict = {}):
    style = stylesheet_file.read()
    for key, value in style_variables.items():
        style = style.replace(key, value)

    return style


def update_styles(app: QApplication):
    style_variables = {}
    with open(STYLE_VARIABLES) as style_variables_file:
        for line in style_variables_file:
            key, value = line.split("=")
            style_variables[key] = value

    with open(QSS_STYLESHEET) as stylesheet_file:
        app.setStyleSheet(
            _load_styles(stylesheet_file, style_variables=style_variables)
        )


def generate_resource_file():
    # Generate QRC file
    print("\nCreating QRC file...")
    lines = ['<!DOCTYPE RCC>\n<RCC version="1.0">\n<qresource>']
    template = "    <file>{file}</file>"
    for file in sorted(IMAGES.iterdir()):
        lines.append(template.format(file=file.relative_to(CWD)))

    lines.append("</qresource>\n</RCC>\n")
    new_data = "\n".join(lines)

    with open(IMAGES_QRC, "r") as fh:
        current_data = fh.read()

    if current_data != new_data:
        with open(IMAGES_QRC, "w") as fh:
            fh.write()

    # Generate resources file from QRC file
    print("Generating resources file from QRC file...")
    check_call(["pyrcc5", "images.qrc", "-o", "images.py"], cwd=CWD)

    # Replace PyQt5 imports with qtpy
    print("Fxing import on resources file...\n")
    with open(IMAGES_PY) as fh:
        data = fh.read()

    with open(IMAGES_PY, "w") as fh:
        fh.write(data.replace("from PyQt5 import QtCore", "from qtpy import QtCore"))
