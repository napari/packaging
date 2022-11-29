from constructor_manager_cli.utils.anaconda import (
    conda_package_data,
    conda_package_versions,
)


def test_conda_package_data():
    package = "napari"
    data = conda_package_data(package, channel="conda-forge")
    expected_keys = [
        "app_entry",
        "conda_platforms",
        "full_name",
        "owner",
        "home",
        "source_git_url",
        "source_git_tag",
        "app_type",
        "upvoted",
        "id",
        "app_summary",
        "public",
        "revision",
        "files",
        "package_types",
        "description",
        "releases",
        "html_url",
        "builds",
        "watchers",
        "dev_url",
        "name",
        "license",
        "versions",
        "url",
        "created_at",
        "modified_at",
        "latest_version",
        "summary",
        "license_url",
        "doc_url",
    ]
    assert data["name"] == package
    for key in expected_keys:
        assert key in data


def test_conda_package_versions():
    versions = conda_package_versions("napari", channels=("conda-forge", "napari"))
    assert versions[0] == "0.2.12"


def test_conda_package_versions_build():
    versions = conda_package_versions(
        "napari", "*pyside*", channels=("conda-forge", "napari")
    )
    assert "0.2.12" not in versions
