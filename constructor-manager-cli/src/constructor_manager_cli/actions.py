"""Constructor manager actions."""
import glob
import datetime
import shutil
import uuid
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from functools import lru_cache

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
    get_list_path,
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
        use_mamba: bool = True,
    ):
        self._channels = channels
        self._info: Optional[Dict] = None
        self._platfonm = None
        self._package_name, cv, self._build_string = parse_conda_version_spec(package)
        self._latest_version = None
        self._platform = None

        # If current version not provided, find the latest installed version
        if cv == "":
            installed_versions_builds = get_installed_versions(self._package_name)
            installed_versions = [vb[0] for vb in installed_versions_builds]
            installed_versions = sort_versions(installed_versions, reverse=True)

            if installed_versions:
                cv = installed_versions[0]
            else:
                # If not installed, save the latest version found
                versions = self._check_available_versions()
                if versions:
                    self._latest_version = versions[0]

        self._current_version = cv
        self._installer = CondaInstaller(
            channels=channels, pinned=self._package_name, use_mamba=use_mamba
        )

    @lru_cache
    def _get_info(self) -> Dict:
        """Get conda info."""
        self._info = self._installer.info()
        self._platform = self._info["platform"]
        return self._info

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

    def _create_environment_file_for_locking(self, version, packages) -> Path:
        """Create an environment file for locking.

        Parameters
        ----------
        version : str
            Version to create environment for.
        packages : list of str
            Packages to include in the environment.

        Returns
        -------
        Path
            Path to the environment file.
        """
        if self._platform is None:
            self._get_info()

        dependencies = [f"{p['name']}={p['version']}" for p in packages]
        yaml_spec = {
            "dependencies": dependencies,
            "channels": list(self._channels),
            "platforms": [self._platform],
        }

        env_path = get_env_path() / f"{self._package_name}-{version}-environment.yaml"
        with open(env_path, "w") as f:
            yaml.dump(yaml_spec, f)

        return env_path

    def _create_list_file(self, version) -> None:
        """Create a conda/mamba list file for a given version.

        This use conda/mamba list for the given version and write a yaml file
        if no other files exists, or if the previous file has different
        content.

        Parameters
        ----------
        version : str
            Version to create conda list for.
        """
        date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        path = get_list_path() / f"{self._package_name}-{version}-{date}-list.yaml"
        prefix = get_prefix_by_name(f"{self._package_name}-{version}")
        packages = self._installer.list(str(prefix), block=True)

        # Find all files with the same pattern
        filepaths = glob.glob(
            str(get_list_path() / f"{self._package_name}-{version}-*-list.yaml")
        )

        # Check if the latest file with the same content exists
        data = {}
        for filepath in sorted(filepaths, reverse=True):
            with open(filepath) as f:
                data = yaml.load(f, Loader=yaml.SafeLoader)
            break

        if data != packages:
            with open(path, "w") as f:
                yaml.dump(packages, f)

    def _lock_environment(self, version, packages):
        """
        Lock the environment, using conda lock.
        """
        env_path = self._create_env_for_locking(version, packages)
        date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        lockfile = get_state_path() / f"{self._package_name}-{version}-{date}-lock.yaml"

        self._installer.lock(str(env_path), lockfile=str(lockfile), block=True)

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

    def _create_shortcuts(self, version):
        """Create shortcuts for a given version.

        This assumes that the menu for a given package is a sepparate package
        called ``'<package_name>-menu'`` with the same version.

        Parameters
        ----------
        version : str
            Version to create shortcuts for.
        """
        prefix = get_prefix_by_name(f"{self._package_name}-{version}")
        menu_spec = f"{self._package_name}-menu={version}"
        return self._installer.install(
            prefix, pkg_list=[menu_spec], shortcuts=True, block=True
        )

    def _remove_shortcuts(self, version: str):
        """Remove shortcuts for a given version.

        Parameters
        ----------
        version : str
            Version to remove shortcuts for.
        """
        prefix = get_prefix_by_name(f"{self._package_name}-{version}")
        menu_spec = f"{self._package_name}-menu={version}"
        return self._installer.uninstall(
            pkg_list=[menu_spec], prefix=str(prefix), shortcuts=True, block=True
        )

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

    def _remove(self, version: str, shortcuts: bool = True):
        """Remove specific environment of a given package.

        Environment will be removed using conda/mamba, or the folders deleted in
        case conda fails.

        Shortcuts for the package will also be removed.

        Parameters
        ----------
        version : str
            Package version.
        shortcuts : bool, optional
            If ``True``, remove the shortcuts. Default is ``True``.
        """
        # print("removing sentinel file")
        # Remove the sentinel file of the old environment
        remove_sentinel_file(self._package_name, version)

        # Remove the shortcuts of the old environment
        if shortcuts:
            # print('removing shortcuts')
            self._remove_shortcuts(version)

        # Try to remove using conda/mamba
        prefix = get_prefix_by_name(f"{self._package_name}-{version}")
        # print('removing env with conda')
        self._installer.remove(str(prefix), block=True)

        # Otherwise rename and remove the folder manually
        if prefix.exists():
            # print('renaming for later removal')
            prefix.rename(prefix.parent / f"{prefix.name}-{uuid.uuid1()}")

    def _create(self, spec, shortcuts: bool = True):
        """"""
        package_name, version, _ = parse_conda_version_spec(spec)
        prefix = get_prefix_by_name(f"{package_name}-{version}")
        self._log(f"Creating environment {prefix}...")
        self._installer.create(str(prefix), pkg_list=[spec], block=True)

        # Lock environment
        # TODO:

        # Create the shortcuts for the new environment
        if shortcuts:
            self._create_shortcuts(version=version)

        # Create the sentinel file for the new environment
        create_sentinel_file(self._package_name, version)

    def _check_available_versions(self, dev: bool = False) -> List[str]:
        """Check for available versions.

        Parameters
        ----------
        dev : bool, optional
            If ``True``, check for development versions. Default is ``False``.

        Returns
        -------
        list
            List of available versions.
        """
        self._log("Checking available versions...")
        versions = conda_package_versions(
            self._package_name,
            build=self._build_string,
            channels=self._channels,
            reverse=True,
        )

        if not dev:
            versions = list(filter(is_stable_version, versions))

        return versions

    def _log(self, msg):
        """Log message to console stderr."""
        prefix = f"constructor-manager-cli ({self._package_name}): "
        suffix = "\n"
        sys.stderr.write(f"{prefix}{msg}{suffix}")

    # --- Plugin API
    # ------------------------------------------------------------------------
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
        versions = self._check_available_versions(dev)
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
            # Refers to the latest version that is newer than the current
            "update": update,
            "installed": latest_version in installed_versions,
        }

    def check_version(self) -> Dict:
        """Return the currently installed version."""
        # TODO: Add modified date? This needs the lock file date
        self._log("Checking version...")
        return {"version": self._current_version}

    def check_packages(self, plugins_url: Optional[str] = None) -> Dict:
        """Check for installed packages.

        Parameters
        ----------
        plugins_url : str, optional
            URL with list of plugins avaliable for package. Default is ``None``.
            This endpoint should return a JSON object with the name of the plugins
            as keys, or a JSON Array with the names of the plugins.

        Returns
        -------
        list
            List of installed packages.
        """
        self._log("Checking prefix exists...")
        prefix = get_prefix_by_name(f"{self._package_name}-{self._current_version}")
        if not prefix.exists():
            return {}

        self._log("Getting installed packages info...")
        return {"packages": self._get_installed_packages(prefix, plugins_url)}

    def check_status(self):
        """Get status of any running action."""
        # TODO:

    def update(
        self,
        plugins_url: Optional[str] = None,
        dev: bool = False,
    ) -> Dict:
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

    def restore(self) -> Dict:
        pass

    def revert(self) -> Dict:
        pass

    def reset(self) -> Dict:
        """Reset environment."""
        # Remove any pending broken envs
        self._log("Cleaning any broken environments...")
        self.clean_all()

        version = (
            self._current_version if self._current_version else self._latest_version
        )

        # Remove the old environment
        self._log("Removing environment...")
        prefix = get_prefix_by_name(f"{self._package_name}-{version}")
        if prefix.exists():
            self._remove(version=self._current_version)

        # Create the new environment
        self._log("Creating new environment...")
        spec = f"{self._package_name}={version}=*{self._build_string}*"
        self._create(spec)

        # Remove any pending broken envs
        self._log("Cleaning any broken environments...")
        self.clean_all()

        return "Environment reset complete!"

    def clean_all(self) -> Dict:
        """Clean all environments of a given package.

        Environments will be removed using conda/mamba, or the folders deleted in
        case conda fails.

        Parameters
        ----------
        package_name : str
            Name of the package.
        """
        for prefix in get_broken_envs(self._package_name):
            shutil.rmtree(prefix, ignore_errors=True)
