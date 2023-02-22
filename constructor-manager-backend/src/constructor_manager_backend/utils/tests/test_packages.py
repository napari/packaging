import pytest
from constructor_manager_cli.utils.packages import normalized_name, sentinel_file_name


def test_sentinel_file_name():
    assert sentinel_file_name("foo") == ".foo_is_bundled_constructor"


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("napari_svg", "napari-svg"),
        ("napari.svg", "napari-svg"),
        ("napari-SVG", "napari-svg"),
        ("napari_SVG.2", "napari-svg-2"),
    ],
)
def test_normalized_name(test_input, expected):
    assert normalized_name(test_input) == expected
