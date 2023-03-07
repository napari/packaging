import random
import shutil

import pytest
from constructor_manager.installer import CondaInstaller
from constructor_manager.utils.conda import get_base_prefix, get_prefix_by_name


def test_conda_installer_info():
    data = CondaInstaller().info()
    assert data["conda_prefix"] == str(get_base_prefix())


def test_conda_installer_list():
    pkgs = CondaInstaller().list(get_base_prefix(), block=True)
    pkg_names = [pkg["name"] for pkg in pkgs]
    assert pkgs
    assert "conda" in pkg_names
    assert "mamba" in pkg_names


@pytest.mark.parametrize("use_mamba", [True, False])
def test_conda_installer_create_remove(use_mamba):
    prefix = get_prefix_by_name(
        f"test-constructor-manager-{random.randint(1000, 9999)}"
    )
    if prefix.exists() and prefix.is_dir():
        shutil.rmtree(prefix)
    shutil.rmtree(prefix, ignore_errors=True)

    installer = CondaInstaller(use_mamba=use_mamba)
    # Create
    _ = installer.create(prefix=prefix, block=True)
    assert prefix.exists()
    # assert installer._exit_codes[job_id] == 0

    # Remove
    _ = installer.remove(prefix=prefix, block=True)
    assert not prefix.exists()
    # assert installer._exit_codes[job_id] == 0


@pytest.mark.parametrize("use_mamba", [True, False])
def test_conda_installer_install_uninstall(use_mamba):
    prefix = get_base_prefix()
    pkg = "loghub"
    installer = CondaInstaller(use_mamba=use_mamba)

    # Install
    _ = installer.install([pkg], prefix=prefix, block=True)

    pkgs = installer.list(prefix=prefix, block=True)
    print("HELLO", pkgs)
    pkg_names = [pkg["name"] for pkg in pkgs]
    assert pkg in pkg_names

    # Uninstall
    _ = installer.uninstall([pkg], prefix=prefix, block=True)
    pkgs = installer.list(prefix=prefix, block=True)
    print("HELLO 2", pkgs)
    pkg_names = [pkg["name"] for pkg in pkgs]
    assert pkg not in pkg_names
