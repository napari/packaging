from constructor_manager.utils.conda import get_base_prefix


def test_worker():
    assert get_base_prefix()
