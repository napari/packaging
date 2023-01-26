"""Constructor manager actions."""
import datetime
import shutil
from typing import Dict, List, Optional, Tuple

import yaml

from constructor_manager_cli.defaults import DEFAULT_CHANNEL
from constructor_manager_cli.installer import CondaInstaller
from constructor_manager_cli.utils.request import plugin_versions
from constructor_manager_cli.utils.anaconda import conda_package_versions
from constructor_manager_cli.utils.conda import (
    get_prefix_by_name,
    parse_conda_version_spec,
)
from constructor_manager_cli.utils.io import (
    create_sentinel_file,
    get_broken_envs,
    get_env_path,
    get_installed_versions,
    get_state_path,
    remove_sentinel_file,
)
from constructor_manager_cli.utils.versions import (
    is_stable_version,
    parse_version,
    sort_versions,
)


class ActionManager:
    """Manage constructor based installer actions.

    Package specification, channels and the use of mamba are set once on
    instantiation, and prepares conda info for use in the actions.
    """

    def __init__(
        self,
        package,
        channels: Tuple[str] = (DEFAULT_CHANNEL,),
        use_mamba: bool = False,
    ):
        self._channels = channels
        self._info = None
        self._platfonm = None
        pn, cv, bs = parse_conda_version_spec(package)

        # If current version not provided, find the latest installed version
        if cv == "":
            installed_versions_builds = get_installed_versions(pn)
            installed_versions = [vb[0] for vb in installed_versions_builds]
            installed_versions = sort_versions(installed_versions, reverse=True)
            if installed_versions:
                cv = installed_versions[0]
            else:
                # FIXME: What to do if no version is installed? Raise an error?
                cv = ""

        self._package_name, self._current_version, self._build_string = pn, cv, bs
        self._installer = CondaInstaller(
            channels=channels, pinned=pn, use_mamba=use_mamba
        )

    def get_info(self):
        self._info = self._installer.info()
        self._platform = self._info["platform"]

    def _get_installed_packages(self, prefix, plugins_url: Optional[str] = None):
        """Return a list of installed packages for the given prefix.

        Sumamrizes information to be used by constructor updater UI.

        Parameters
        ----------
        prefix : str
            The prefix to check for plugins.
        plugins_url : str
            The URL to the plugins JSON file.
        with_version : bool, optional
            If True, return the plugin name and version.

        Returns
        -------
        list of str
            The list of installed plugins.
        """
        packages = []
        available_plugins = []
        if plugins_url:
            available_plugins = plugin_versions(plugins_url)

        all_packages = self._installer.list(str(prefix), block=True)
        for pkg in all_packages:  # type: ignore
            source = "pip" if pkg["platform"] == "pypi" else "conda"
            package = {
                "name": pkg["name"],
                "version": pkg["version"],
                "build_string": pkg["build_string"],
                "source": source,
                "is_plugin": pkg["name"] in available_plugins,
                # "data": pkg  # FIXME: Add this for debugging?
            }
            packages.append(package)

        return packages

    def _get_installed_plugins(self, prefix, plugins_url, with_version=False):
        """"""
        packages = self._get_installed_packages(prefix, plugins_url)
        if with_version:
            plugins = [
                f"{p['name']}={p['version']}" for p in packages if p["is_plugin"]
            ]
        else:
            plugins = [p["name"] for p in packages if p["is_plugin"]]

        return plugins

    def _lock_environment(self, version, packages):
        """
        Lock the environment, using conda lock.
        """
        dependencies = [f"{p['name']}= {p['version']}" for p in packages]
        yaml_spec = {"dependencies": dependencies}
        yaml_spec["channels"] = list(self._channels)
        platforms = (self._platform,)

        date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        lockfile = get_state_path() / f"{self._package_name}-{version}-{date}-lock.yaml"

        envs_path = get_env_path()
        envs_path.mkdir(parents=True, exist_ok=True)
        env_path = envs_path / f"{self._package_name}-{version}-environment.yaml"
        with open(env_path, "w") as f:
            yaml.dump(yaml_spec, f)

        self._installer.lock(
            str(env_path), platforms=platforms, lockfile=str(lockfile), block=True
        )

        with open(lockfile) as fh:
            lines = fh.read().split("\n")

        # Remove comments on lock file
        lines = [line for line in lines if not line.startswith("#")]
        with open(lockfile, "w") as fh:
            data = "\n".join(lines)
            fh.write(data)

        # Check if a file mathcing the lockfile already exists with same content
        # filepaths = glob.glob(
        #     str(get_state_path() /
        #     f"{self._package_name}-{current_version}-*-lock.yaml")
        # )
        # for filepath in sorted(filepaths, reverse=True):
        #     with open(filepath) as fh:
        #         if str(lockfile) != filepath and fh.read() == data:
        #             lockfile.unlink()
        #             break

    def _create_shortcuts(self):
        pass

    def _remove_shortcuts(self):
        pass

    def _create_with_plugins(
        self,
        version: str,
        plugins: List[str] = [],
    ):
        """Update the package.

        Parameters
        ----------
        version : str
            The package name and version spec.
        plugins : list
            List of plugins to install.

        Returns
        -------
        int
            The return code of the installer.
        """
        # package_name, version = parse_conda_version_spec(package)
        spec = f"{self._package_name}={version}=*{self._build_string}*"
        prefix = get_prefix_by_name(f"{self._package_name}-{version}")
        packages = [spec] + plugins
        job_id = self._installer.create(str(prefix), pkg_list=packages)
        return self._installer._exit_codes[job_id]

    def _create_with_plugins_one_by_one(
        self,
        version: str,
        plugins: List[str] = [],
    ):
        """Update the package.

        Parameters
        ----------
        version : str
            Version to install.
        plugins : list
            List of plugins to install.

        Returns
        -------
        int
            The return code of the installer.
        """
        spec = f"{self._package_name}={version}=*{self._build_string}*"
        prefix = get_prefix_by_name(f"{self._package_name}-{version}")

        job_id = self._installer.create(str(prefix), pkg_list=[spec])
        for plugin in plugins:
            self._installer.install(str(prefix), pkg_list=[plugin])

        return self._installer._exit_codes[job_id]

    def check_updates(self, dev: bool = False) -> Dict:
        """Check for package updates.

        Parameters
        ----------
        dev : bool, optional
            If ``True``, check for development versions. Default is ``False``.

        Returns
        -------
        dict
            Dictionary containing the current and latest versions, found
            installed versions.
        """
        versions = conda_package_versions(
            self._package_name,
            build=self._build_string,
            channels=self._channels,
            reverse=True,
        )

        if not dev:
            versions = list(filter(is_stable_version, versions))

        update = False
        latest_version = versions[0] if versions else ""
        installed_versions_builds = get_installed_versions(self._package_name)
        installed_versions = [vb[0] for vb in installed_versions_builds]
        update = parse_version(latest_version) > parse_version(self._current_version)
        filtered_version = versions[:]
        previous_version: Optional[str] = None
        if self._current_version in filtered_version:
            index = filtered_version.index(self._current_version)
            if (index + 1) < len(filtered_version):
                previous_version = filtered_version[index + 1]
            else:
                previous_version = None

        return {
            "available_versions": versions,
            "current_version": self._current_version,
            "latest_version": latest_version,
            "previous_version": previous_version,
            "installed_versions": installed_versions,
            "status": {
                "data": "",
                "stdout": "",
                "stderr": "",
            },
            # Referes to the latest version that is newer than the current
            "update": update,
            "installed": latest_version in installed_versions,
        }

    def check_version(self):
        """Return the currently installed version."""
        # TODO: Add modified date?
        return {"version": self._current_version}

    def check_packages(self, plugins_url: Optional[str] = None):
        """Check for installed packages.

        Parameters
        ----------
        plugins_url : str, optional
            URL with list of plugins avaliable for package. Default is ``None``.

        Returns
        -------
        list
        """
        prefix = get_prefix_by_name(f"{self._package_name}-{self._current_version}")
        return {"packages": self._get_installed_packages(prefix, plugins_url)}

    def check_status(self):
        """Get status of any running action."""

    def update(
        self,
        plugins_url: Optional[str] = None,
        dev: bool = False,
    ):
        """Update the package.

        Parameters
        ----------
        plugins_url : str
            URL with list of plugins avaliable for package. Default is ``None``.
        dev : bool, optional
            If ``True``, check for development versions. Default is ``False``.

        Returns
        -------
        int
            The return code of the installer.
        """
        data = self.check_updates(dev=dev)
        latest_version = data["latest_version"]

        # This does not check for existence of prefix
        prefix = get_prefix_by_name(f"{self._package_name}-{self._current_version}")
        available_plugins = []
        if plugins_url:
            available_plugins = self._get_installed_plugins(prefix, plugins_url)

        # First try to install everything at once
        return_code = self._create_with_plugins(latest_version, available_plugins)

        # Then try to install plugin by plugin if it failed
        if bool(return_code):
            # TODO: Erase any folder?
            return_code = self._create_with_plugins_one_by_one(
                latest_version,
                available_plugins,
            )

        # Now run an environment lock if it succeeded
        # TODO: Use all packages found in the environment?
        new_prefix = get_prefix_by_name(f"{self._package_name}-{latest_version}")
        available_plugins = []
        if plugins_url:
            available_plugins = self._get_installed_plugins(
                new_prefix, plugins_url, with_version=True
            )

        available_packages = self._get_installed_packages(new_prefix, plugins_url)
        if not bool(return_code):
            self._lock_environment(latest_version, available_packages)
        else:
            pass
            # FIXME: Raise exception??

        # Then delete the sentinel file in the old environment
        remove_sentinel_file(self._package_name, self._current_version)

        # TODO: This part could also be deferred when calling the update
        # process directly from the application
        # Remove the shortcuts from the old environment
        # self._remove_shortcuts(self._package_name, self._current_version)

        # Create shortcuts for the new environment
        # self._create_shortcuts(self._package_name, latest_version)

        # Then create a sentinel file in the the new environment
        create_sentinel_file(self._package_name, latest_version)


def clean_all(package):
    """Clean all environments of a given package.

    Environments will be removed using conda/mamba, or the folders deleted in
    case conda fails.

    Parameters
    ----------
    package_name : str
        Name of the package.
    """
    package_name, _, _ = parse_conda_version_spec(package)
    installer = CondaInstaller()
    failed = []
    for prefix in get_broken_envs(package_name):
        # Try to remove using conda/mamba
        job_id = installer.remove(prefix)
        if installer._exit_codes[job_id]:
            failed.append(prefix)

    # Otherwise remove the folders manually
    for prefix in failed:
        shutil.rmtree(prefix)


# def check_updates_clean_and_launch(
#     package: str,
#     dev: bool = False,
#     channel=DEFAULT_CHANNEL,
# ):
#     """Check for updates and clean."""
#     package_name, version, _ = parse_conda_version_spec(package)
#     res = check_updates(package_name, dev, channel)
#     found_versions = res["found_versions"]

#     # Remove any prior installations
#     if res["installed"]:
#         for version in found_versions:
#             if version != res["latest_version"]:
#                 remove_sentinel_file(package_name, version)

#         # Launch the detached application
#         # print(f"launching {package_name} version {res['latest_version']}")

#         # Remove any prior installations
#         clean_all(package_name)


def remove(package: str, use_mamba: bool = False):
    """Remove specific environment of a given package.

    Environment will be removed using conda/mamba, or the folders deleted in
    case conda fails.

    Parameters
    ----------
    package : str
        Package specification.
    """
    # Try to remove using conda/mamba
    installer = CondaInstaller(use_mamba=use_mamba)
    package_name, version, _ = parse_conda_version_spec(package)
    prefix = get_prefix_by_name(f"{package_name}-{version}")
    job_id = installer.remove(str(prefix))

    # Otherwise remove the folder manually
    if job_id:
        shutil.rmtree(prefix)


# def restore(package: str, channels: Tuple[str] = (DEFAULT_CHANNEL,)):
#     """Restore specific environment of a given package.

#     Parameters
#     ----------
#     package : str
#         Name of the package.
#     channels : tuple of str, optional
#         Check for available versions on these channels.
#         Default is ``('conda-forge', )``.
#     """
#     package_name, current_version, _ = parse_conda_version_spec(package)
#     env_name = f"{package_name}-{current_version}"
#     prefix = str(get_prefix_by_name(env_name))
#     installer = CondaInstaller(channels=channels)
#     job_id_remove = None
#     broken_prefix = ""

#     # Remove with conda/mamba
#     if os.path.isdir(prefix):
#         job_id_remove = installer.remove(prefix)

#     # Otherwise rename the folder manually for later deletion
#     if job_id_remove and os.path.isdir(prefix):
#         broken_prefix = prefix + "-broken"
#         os.rename(prefix, broken_prefix)

#     # Create restored enviornment
#     job_id_restore = installer.create([package], prefix=prefix)

#     # Remove the broken folder manually
#     if broken_prefix and job_id_remove and os.path.isdir(broken_prefix):
#         # print("removing", broken_prefix)
#         shutil.rmtree(broken_prefix)

#     # Create a lock file for the restored environment
#     lock_environment(f"{package_name}={current_version}", channels=channels)
#     create_sentinel_file(package_name, current_version)
#     return installer._exit_codes[job_id_restore]


# if __name__ == "__main__":
#     package = "napari=0.4.15=*pyside*"
#     manager = ActionManager(package, ('conda-forge', ))
#     print(manager.check_updates())
