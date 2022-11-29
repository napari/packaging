import sys

import pytest

from constructor_manager_cli.utils.conda import (
    get_base_prefix,
    get_prefix_by_name,
    parse_conda_version_spec,
)


def test_get_base_prefix():
    assert str(get_base_prefix()) == sys.prefix


def test_get_prefix_by_name():
    assert get_prefix_by_name() == get_base_prefix()
    assert get_prefix_by_name("base") == get_base_prefix()
    assert get_prefix_by_name("foo") == get_base_prefix() / "envs" / "foo"


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("napari=0.4.1=*pyside*", ("napari", "0.4.1", "*pyside*")),
        ("napari=0.4.1", ("napari", "0.4.1", "")),
        ("napari=*=*pyside*", ("napari", "", "*pyside*")),
        ("napari", ("napari", "", "")),
    ],
)
def test_parse_conda_version_spec(test_input, expected):
    assert parse_conda_version_spec(test_input) == expected
