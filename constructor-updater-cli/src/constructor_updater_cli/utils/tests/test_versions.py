import pytest
from constructor_updater_cli.utils.versions import is_stable_version


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("0.4", True),
        ("0.4.15", True),
        ("0.4.15rc1", False),
        ("0.4.15dev0", False),
        ("0.4.15beta", False),
        ("0.4.15alfa", False),
        (("0", "4"), True),
        (("0", "4", "15"), True),
        (("0", "4", "15", "rc1"), False),
        (("0", "4", "15", "beta"), False),
    ],
)
def test_is_stable_version(test_input, expected):
    assert is_stable_version(test_input) == expected
