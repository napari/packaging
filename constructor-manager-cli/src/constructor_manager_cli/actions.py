"""Constructor manager actions."""
import glob
import datetime
import shutil
import uuid
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from functools import lru_cache
import logging

import yaml

from constructor_manager_cli.defaults import DEFAULT_CHANNEL
from constructor_manager_cli.installer import CondaInstaller
from constructor_manager_cli.utils.request import plugin_versions
from constructor_manager_cli.utils.anaconda import conda_package_versions
from constructor_manager_cli.utils.conda import (
    get_prefix_by_name,
    parse_conda_version_spec,
)
from constructor_manager_cli.utils.shortcuts import open_application
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


logger = logging.getLogger(__name__)


class EnvironmentDoesNotExist(Exception):
    pass


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

    def _get_installed_packages(
        self, prefix, plugins_url: Optional[str] = None
    ) -> Tuple:
        """Return a list of installed packages for the given prefix.

        Summarizes information to be used by constructor updater UI.

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
        package_simplified_format = []
        available_plugins = []
        if plugins_url:
            available_plugins = plugin_versions(plugins_url)

        packages_original_format = self._installer.list(str(prefix), block=True)
        for pkg in packages_original_format:  # type: ignore
            source = "pip" if pkg["platform"] == "pypi" else "conda"
            package = {
                "name": pkg["name"],
                "version": pkg["version"],
                "build_string": pkg["build_string"],
                "source": source,
                "is_plugin": pkg["name"] in available_plugins,
            }
            package_simplified_format.append(package)

        return package_simplified_format, packages_original_format

    def _get_installed_plugins_name_version_dict(self, prefix, plugins_url):
        """"""
        (
            package_simplified_format,
            packages_original_format,
        ) = self._get_installed_packages(prefix, plugins_url)
        return [
            p for p in package_simplified_format if p["is_plugin"]
        ], packages_original_format

    def _get_installed_plugins(self, prefix, plugins_url, with_version=False):
        """"""
        packages, _ = self._get_installed_packages(prefix, plugins_url)
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

        env_path = get_env_path() / f"{self._package_name}-{version}-environment.yml"
        with open(env_path, "w") as f:
            yaml.dump(yaml_spec, f)

        return env_path

    # def _create_list_file(self, version) -> None:
    #     """Create a conda/mamba list file for a given version.

    #     This use conda/mamba list for the given version and write a yaml file
    #     if no other files exists, or if the previous file has different
    #     content.

    #     Parameters
    #     ----------
    #     version : str
    #         Version to create conda list for.
    #     """
    #     date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    #     path = get_list_path() / f"{self._package_name}-{version}-{date}-list.yaml"
    #     prefix = get_prefix_by_name(f"{self._package_name}-{version}")
    #     packages = self._installer.list(str(prefix), block=True)

    #     # Find all files with the same pattern
    #     filepaths = glob.glob(
    #         str(get_list_path() / f"{self._package_name}-{version}-*-list.yaml")
    #     )

    #     # Check if the latest file with the same content exists
    #     data = {}
    #     for filepath in sorted(filepaths, reverse=True):
    #         with open(filepath) as f:
    #             data = yaml.load(f, Loader=yaml.SafeLoader)
    #         break

    #     if data != packages:
    #         with open(path, "w") as f:
    #             yaml.dump(packages, f)

    # Environment locking
    # -------------------------------------------------------------------------
    def _lock_environment(self, version, packages, date=None):
        """
        Lock the environment, using conda lock.
        """
        date = date or datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

        # Include the application
        application = {"name": self._package_name, "version": version}
        packages = [application] + packages
        env_path = self._create_environment_file_for_locking(version, packages)

        lockfile = get_state_path() / f"{self._package_name}-{version}-{date}-lock.yml"
        temp_lockfile = (
            get_state_path() / f"{self._package_name}-{version}-{date}-temp.yml"
        )
        self._installer.lock(
            env_path=str(env_path), lockfile=str(temp_lockfile), block=True
        )

        with open(temp_lockfile) as fh:
            lines = fh.read().split("\n")

        # Remove comments on lock file
        lines = [line for line in lines if not line.startswith("#")]
        with open(temp_lockfile, "w") as fh:
            data = "\n".join(lines)
            fh.write(data)

        # Rename to remove the temp name
        temp_lockfile.rename(lockfile)

    def _should_lock(self, version, packages):
        lists = self._get_available_lists(version)
        if lists:
            with open(lists[0]) as fh:
                data = yaml.load(fh, Loader=yaml.SafeLoader)

            return data != packages

        return True

    def _get_available_lists(self, version):
        # TODO: Check that there is a corresponding state file with the same date,
        # otherwise, it means that a lock file process could not be completed
        # succesfully
        return glob.glob(
            str(get_list_path() / f"{self._package_name}-{version}-*-list.yml")
        )

    def _get_available_states(self) -> Dict:
        """Get available states and group them by version."""
        pattern = f"{self._package_name}-*-lock.yml"
        paths = [Path(p).name for p in glob.glob(str(get_state_path() / pattern))]
        versions = set()
        for path in paths:
            versions.add(path.replace(f"{self._package_name}-", "").split("-")[0])

        data = {}  # type: ignore
        for version in sorted(versions, reverse=True):
            data[version] = []

            for path in paths:
                prefix = f"{self._package_name}-{version}-"
                suffix = "-lock.yml"
                if path.startswith(prefix):
                    path = path.replace(prefix, "").replace(suffix, "")
                    data[version].append(str(path))

        return data

    # Shortcuts
    # -------------------------------------------------------------------------
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

    # Install
    # -------------------------------------------------------------------------
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
        logger.debug(f"Creating environment {prefix}...")
        self._installer.create(str(prefix), pkg_list=[spec], block=True)

        # Lock environment
        # TODO:

        # Create the shortcuts for the new environment
        if shortcuts:
            self._create_shortcuts(version=version)

        # Create the sentinel file for the new environment
        create_sentinel_file(self._package_name, version)

    # Other
    # -------------------------------------------------------------------------
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
        logger.debug("Checking available versions...")
        versions = conda_package_versions(
            self._package_name,
            build=self._build_string,
            channels=self._channels,
            reverse=True,
        )

        if not dev:
            versions = list(filter(is_stable_version, versions))

        return versions

    # --- API
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
            "states": self._get_available_states(),
            # Refers to the latest version that is newer than the current
            "update": update,
            "installed": latest_version in installed_versions,
        }

    def check_version(self) -> Dict:
        """Return the currently installed version."""
        # TODO: Add modified date? This needs the lock file date
        logger.debug("Checking version...")
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
        logger.debug("Checking prefix exists...")
        prefix = get_prefix_by_name(f"{self._package_name}-{self._current_version}")
        if not prefix.exists():
            return {}

        logger.debug("Getting installed packages info...")
        packages, _ = self._get_installed_packages(prefix, plugins_url)
        return {"packages": packages}

    def check_status(self):
        """Get status of any running action."""
        return {}

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

        print(available_plugins)
        # First try to lock everything at once

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
        self._remove_shortcuts(self._package_name, self._current_version)

        # Create shortcuts for the new environment
        self._create_shortcuts(self._package_name, latest_version)

        # Then create a sentinel file in the the new environment
        create_sentinel_file(self._package_name, latest_version)
        return {}

    def restore(self) -> Dict:
        """Restore to a previously saved store point for the same version.

        This will only run if any restore points are found
        """
        # lists, states = self._get_available_lists_and_states(self._current_version)
        return {}

    def revert(self) -> Dict:
        """Restore to a previously saved store point for the previous version.

        This will only run if any restore points are found
        """
        # lists, states = self._get_available_lists_and_states(self._current_version)
        return {}

    def reset(self) -> str:
        """Reset environment."""
        # Remove any pending broken envs
        logger.debug("Cleaning any broken environments...")
        self.clean_all()

        version = (
            self._current_version if self._current_version else self._latest_version
        )

        # Remove the old environment
        logger.debug("Removing environment...")
        prefix = get_prefix_by_name(f"{self._package_name}-{version}")
        if prefix.exists():
            self._remove(version=self._current_version)

        # Create the new environment
        logger.debug("Creating new environment...")
        spec = f"{self._package_name}={version}=*{self._build_string}*"
        self._create(spec)

        # Remove any pending broken envs
        logger.debug("Cleaning any broken environments...")
        self.clean_all()

        return "Environment reset complete!"

    def lock_environment(
        self,
        version: str,
        plugins_url: Optional[str] = None,
    ):
        """Lock environment.

        Parameters
        ----------
        version : str
            TODO
        packages : list
            TODO
        update : bool, optional
            If ``True``, update the lock file. Default is ``False``.
        """
        logger.debug("Locking environment...")
        prefix = get_prefix_by_name(f"{self._package_name}-{version}")
        if not prefix.exists():
            raise EnvironmentDoesNotExist(f"Environment '{prefix}' does not exist!")

        # FIXME: Should this only compare plugin changes?
        logger.debug("Getting installed plugins...")
        plugins, packages = self._get_installed_plugins_name_version_dict(
            prefix, plugins_url
        )

        # TODO: Do we need to lock?, did the env listing change with respect
        # to the latest state file found?
        logger.debug("Should lock environment...?")
        should_lock = self._should_lock(version, packages)

        if should_lock:
            logger.debug("locking environment...")
            date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

            # Create a temporary list file
            temp_list_path = (
                get_list_path() / f"{self._package_name}-{version}-{date}-temp.yml"
            )
            list_path = (
                get_list_path() / f"{self._package_name}-{version}-{date}-list.yml"
            )
            with open(temp_list_path, "w") as fh:
                yaml.dump(packages, fh)

            logger.debug("locking...")
            self._lock_environment(version, plugins, date)

            # Remove the temporary mark from list if successful
            logger.debug("renaming temp...")
            temp_list_path.rename(list_path)

        else:
            logger.debug("no locking needed...")

        return

    def clean_all(self) -> Dict:
        """Clean all environments of a given package.

        Environments will be removed using conda/mamba, or the folders deleted in
        case conda fails.

        Parameters
        ----------
        package_name : str
            Name of the package.
        """
        # Remove any broken envs
        for prefix in get_broken_envs(self._package_name):
            shutil.rmtree(prefix, ignore_errors=True)

        # TODO: Remove all data from the constructor manager config

        # TODO: Remove all the temp states and list files

        # Add actions taken by the clean all command
        return {}

    def uninstall(self) -> Dict:
        """Uninstall the bundle application."""
        # Remove all shortcuts

        # Remove all the application environments

        # Remove the constructor environment

        # Remove the base environment

        # Remove everything else with rm rf $CONDA_PREFIX

    def open(self) -> Dict:
        """Open the bundle application with package name and version."""
        exit_code = open_application(self._package_name, self._current_version)
        return {"exit_code": exit_code}


if __name__ == "__main__":
    manager = ActionManager("napari=0.4.16")
    # packages = [
    #     {
    #         "name": "napari-console",
    #         "version": "0.4.11",
    #     },
    # ]
    # manager.lock_environment(
    #     "0.4.16",
    #     plugins_url="https://api.napari-hub.org/plugins",
    # )
    print(manager._get_available_states())

    # print(manager._get_available_lists("0.4.16"))
    # manager._create_list(        "0.4.16",)
    # print(manager._should_lock("0.4.16"))
