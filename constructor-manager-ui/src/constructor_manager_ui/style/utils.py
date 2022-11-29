"""Utility functions to update and load the application style."""

from pathlib import Path
from typing import Dict

from qtpy.QtWidgets import QApplication  # type: ignore

# UI style constant
STYLE_VARIABLES = Path(__file__).parent / "style_variables.txt"
QSS_STYLESHEET = Path(__file__).parent / "base.qss"


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
