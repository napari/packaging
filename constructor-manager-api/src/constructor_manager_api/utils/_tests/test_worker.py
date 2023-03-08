from constructor_manager_api.utils.conda import get_base_prefix


def test_worker():
    assert get_base_prefix()
