"""Constructor manager actions."""
import datetime
import glob
import logging
import shutil
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from constructor_manager.defaults import DEFAULT_CHANNEL
from constructor_manager.installer import CondaInstaller
from constructor_manager.utils.anaconda import conda_package_versions
from constructor_manager.utils.conda import (
    get_prefix_by_name,
    parse_conda_version_spec,
)
from constructor_manager.utils.io import (
    create_sentinel_file,
    get_broken_envs,
    get_env_path,
    get_installed_versions,
    get_list_path,
    get_state_path,
    remove_sentinel_file,
)
from constructor_manager.utils.request import plugin_versions
from constructor_manager.utils.shortcuts import (
    create_shortcut,
    open_application,
    remove_shortcut,
)
from constructor_manager.utils.versions import (
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
        application,
        channels: Tuple[str] = (DEFAULT_CHANNEL,),
        use_mamba: bool = True,
    ):
        self._channels = channels
        self._info: Optional[Dict] = None
        self._platfonm = None
        self._application_name, cv, self._build_string = parse_conda_version_spec(
            application
        )
        self._latest_version = None
        self._platform = None

        # If current version not provided, find the latest installed version
        if cv == "":
            installed_versions_builds = get_installed_versions(self._application_name)
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
            channels=channels, pinned=self._application_name, use_mamba=use_mamba
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
        logger.debug(f"Getting installed packages for {prefix}...")
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

        env_path = (
            get_env_path() / f"{self._application_name}-{version}-environment.yml"
        )
        with open(env_path, "w") as f:
            yaml.dump(yaml_spec, f)

        return env_path

    # Environment locking
    # -------------------------------------------------------------------------
    def _lock_environment(self, version, packages, date=None):
        """
        Lock the environment, using conda lock.
        """
        date = date or datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

        # Include the application
        application = {"name": self._application_name, "version": version}
        packages = [application] + packages
        env_path = self._create_environment_file_for_locking(version, packages)

        lockfile = (
            get_state_path()
            / f"{self._application_name}-{version}-{date}-conda-lock.yml"
        )
        temp_lockfile = (
            get_state_path() / f"{self._application_name}-{version}-{date}-temp.yml"
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
            str(get_list_path() / f"{self._application_name}-{version}-*-list.yml")
        )

    def _get_available_states(self) -> Dict:
        """Get available states and group them by version."""
        pattern = f"{self._application_name}-*-conda-lock.yml"
        paths = [Path(p).name for p in glob.glob(str(get_state_path() / pattern))]
        versions = set()
        for path in paths:
            versions.add(path.replace(f"{self._application_name}-", "").split("-")[0])

        data = {}  # type: ignore
        for version in sorted(versions, reverse=True):
            data[version] = []

            for path in paths:
                prefix = f"{self._application_name}-{version}-"
                suffix = "-conda-lock.yml"
                if path.startswith(prefix):
                    path = path.replace(prefix, "").replace(suffix, "")
                    data[version].append(str(path))

            data[version] = list(sorted(data[version], reverse=True))

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
        prefix = get_prefix_by_name(f"{self._application_name}-{version}")
        menu_spec = f"{self._application_name}-menu={version}"
        rc = self._installer.install(
            prefix, pkg_list=[menu_spec], shortcuts=True, block=True
        )

        # Install shortcuts manually using menuinst
        paths = remove_shortcut(self._application_name, version)
        paths = create_shortcut(self._application_name, version)
        return rc, paths

    def _remove_shortcuts(self, version: str):
        """Remove shortcuts for a given version.

        Parameters
        ----------
        version : str
            Version to remove shortcuts for.
        """
        logger.debug(
            f"Removing shortcuts for version: {self._application_name}={version}"
        )
        paths = remove_shortcut(self._application_name, version)

        logger.debug(f"Removing menu package: {self._application_name}-menu={version}")
        prefix = get_prefix_by_name(f"{self._application_name}-{version}")
        menu_spec = f"{self._application_name}-menu={version}"
        rc = self._installer.uninstall(
            pkg_list=[menu_spec], prefix=str(prefix), shortcuts=True, block=True
        )
        return rc, paths

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
        spec = f"{self._application_name}={version}=*{self._build_string}*"
        prefix = get_prefix_by_name(f"{self._application_name}-{version}")
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
        spec = f"{self._application_name}={version}=*{self._build_string}*"
        prefix = get_prefix_by_name(f"{self._application_name}-{version}")

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
        # Remove the sentinel file of the old environment
        remove_sentinel_file(self._application_name, version)

        # Remove the shortcuts of the old environment
        if shortcuts:
            self._remove_shortcuts(version)

        # Try to remove using conda/mamba
        prefix = get_prefix_by_name(f"{self._application_name}-{version}")
        self._installer.remove(str(prefix), block=True)

        # Otherwise rename and remove the folder manually
        if prefix.exists():
            prefix.rename(prefix.parent / f"{prefix.name}-{uuid.uuid1()}")

    def _create(
        self,
        application_spec,
        plugins: Optional[List[str]] = None,
        plugins_url: Optional[str] = None,
        shortcuts: bool = True,
    ):
        """"""
        plugins = plugins or []
        package_name, version, _ = parse_conda_version_spec(application_spec)
        prefix = get_prefix_by_name(f"{package_name}-{version}")
        logger.debug(f"Creating environment {prefix}...")

        # Try to install all packages at once
        pkg_list = [application_spec] + plugins
        self._installer.create(str(prefix), pkg_list=pkg_list, block=True)

        if not prefix.exists():
            # Try to install the application and then the plugins one by one
            self._installer.create(str(prefix), pkg_list=[application_spec], block=True)

            # TODO: temporary fix, fix the installer!
            if prefix.exists():
                for plugin in plugins:
                    self._installer.install(str(prefix), pkg_list=[plugin], block=True)

        # Lock environment
        self.lock_environment(version=version, plugins_url=plugins_url)

        # Create the shortcuts for the new environment
        if shortcuts:
            self._create_shortcuts(version=version)

        # Create the sentinel file for the new environment
        create_sentinel_file(self._application_name, version)

    def _create_from_lock(self, state_file, version):
        """Create a new environment from a lock file."""
        logger.debug("Removing environment...")
        self._remove(version, shortcuts=True)

        logger.debug(f"Restoring {state_file}...")
        prefix = get_prefix_by_name(f"{self._application_name}-{version}")
        state_path = get_state_path() / state_file
        self._installer.install_from_lock(str(prefix), str(state_path), block=True)
        self._create_shortcuts(version=version)

        # Create the sentinel file for the environment
        create_sentinel_file(self._application_name, version)

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
            self._application_name,
            build=self._build_string,
            channels=self._channels,
            reverse=True,
        )

        if not dev:
            versions = list(filter(is_stable_version, versions))

        return versions

    # --- API
    # ------------------------------------------------------------------------
    def check_updates(
        self,
        dev: bool = False,
        lock_created: Optional[bool] = None,
    ) -> Dict:
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
        installed_versions_builds = get_installed_versions(self._application_name)
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
            "busy": not bool(lock_created),
        }

    def check_version(
        self,
        lock_created: Optional[bool] = None,
    ) -> Dict:
        """Return the currently installed version."""
        # TODO: Add modified date? This needs the lock file date
        logger.debug("Checking version...")
        return {"version": self._current_version}

    def check_packages(
        self,
        plugins_url: Optional[str] = None,
        lock_created: Optional[bool] = None,
    ) -> Dict:
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
        prefix = get_prefix_by_name(f"{self._application_name}-{self._current_version}")
        if not prefix.exists():
            return {}

        logger.debug("Getting installed packages info...")
        packages, _ = self._get_installed_packages(prefix, plugins_url)
        return {"packages": packages}

    def check_status(
        self,
        lock_created: Optional[bool] = None,
    ):
        """Get status of any running action."""
        logger.debug(f"Checking status for {self._application_name}...")
        return {"busy": not bool(lock_created)}

    def update(
        self,
        plugins_url: Optional[str] = None,
        dev: bool = False,
        delayed: bool = False,
        lock_created: Optional[bool] = None,
    ) -> Dict:
        """Update the package.

        Parameters
        ----------
        plugins_url : str
            URL with list of plugins avaliable for package. Default is ``None``.
        dev : bool, optional
            If ``True``, check for development versions. Default is ``False``.
        delayed : bool, optional
            If ``True``, the update will be done in two steps, so that in can be
            done in the backgroun while the main application is running.
            Default is ``False``.

        Returns
        -------
        int
            The return code of the installer.
        """
        shortcuts = not delayed
        logger.debug(f"Checking updates for {self._application_name}...")
        data = self.check_updates(dev=dev)
        latest_version = data["latest_version"]
        installed = data["installed"]  # If `True`, comes from a delayed installation
        application_spec = f"{self._application_name}=={latest_version}"

        old_prefix = get_prefix_by_name(
            f"{self._application_name}-{self._current_version}"
        )
        new_prefix = get_prefix_by_name(f"{self._application_name}-{latest_version}")
        if not installed:
            available_plugins = []
            if plugins_url and old_prefix.exists():
                available_plugins = self._get_installed_plugins(old_prefix, plugins_url)

            logger.debug(f"Available plugins {available_plugins}")

            if new_prefix.exists():
                logger.debug(f"Removing prefix {new_prefix}...")
                self._remove(self._current_version, shortcuts=True)

            logger.debug(f"Creating {new_prefix}...")
            self._create(
                application_spec,
                plugins=available_plugins,
                plugins_url=plugins_url,
                shortcuts=shortcuts,
            )

        logger.debug(f"delayed  {delayed}?...")
        if not delayed:
            logger.debug(f"Removing prefix {old_prefix}...")
            self._remove(self._current_version, shortcuts=shortcuts)

        if installed and delayed:
            logger.debug(f"Creating shorcuts {new_prefix}...")
            self._create_shortcuts(latest_version)

            logger.debug(f"Openning {self._application_name}={latest_version} ...")
            self.open(latest_version)

            logger.debug(f"Removing prefix {old_prefix}...")
            self._remove(self._current_version, shortcuts=True)

        return {}

    def restore(
        self,
        state_file: Optional[str] = None,
        lock_created: Optional[bool] = None,
    ) -> Dict:
        """Restore to a previously saved store point for the same version.

        This will only run if any restore points are found
        """
        logger.debug("Restoring environment...")
        states = self._get_available_states()
        for version, states in states.items():
            for state in states:
                state_file_check = (
                    f"{self._application_name}-{version}-{state}-conda-lock.yml"
                )
                if state_file is None:
                    break

                if state_file_check == state_file:
                    self._create_from_lock(state_file, version=version)
                    return {}

            if state_file is None:
                self._create_from_lock(state_file_check, version=version)
                return {}

        return {}

    def revert(
        self,
        lock_created: Optional[bool] = None,
    ) -> Dict:
        """Restore to a previously saved store point for the previous version.

        This will only run if any restore points are found
        """
        states = self._get_available_states()
        state = None
        version = None
        for version, states in states.items():
            if parse_version(version) < parse_version(self._current_version):
                version = version
                state = states[0]
                break

        if state:
            state_file = f"{self._application_name}-{version}-{state}-conda-lock.yml"
            logger.debug(f"Reverting to {state_file}...")
            self.restore(state_file)

            logger.debug("Removing old environment...")
            self._remove(self._current_version, shortcuts=True)

        return {}

    def reset(
        self,
        lock_created: Optional[bool] = None,
    ) -> str:
        """Reset environment."""
        logger.debug("Cleaning environments...")
        self.clean_all()

        version = (
            self._current_version if self._current_version else self._latest_version
        )

        logger.debug("Removing environment...")
        prefix = get_prefix_by_name(f"{self._application_name}-{version}")
        if prefix.exists():
            self._remove(version=self._current_version)

        logger.debug("Creating new environment...")
        spec = f"{self._application_name}={version}=*{self._build_string}*"
        self._create(spec, plugins_url=None)

        logger.debug("Cleaning environments...")
        self.clean_all()

        return "Environment reset complete!"

    def lock_environment(
        self,
        version: Optional[str] = None,
        plugins_url: Optional[str] = None,
        lock_created: Optional[bool] = None,
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
        version = self._current_version if version is None else version
        prefix = get_prefix_by_name(f"{self._application_name}-{version}")
        if not prefix.exists():
            raise EnvironmentDoesNotExist(f"Environment '{prefix}' does not exist!")

        # FIXME: Should this only compare plugin changes?
        logger.debug("Getting installed plugins...")
        plugins, packages = self._get_installed_plugins_name_version_dict(
            prefix, plugins_url
        )

        logger.debug("Should lock environment...?")
        should_lock = self._should_lock(version, packages)

        if should_lock:
            logger.debug("locking environment...")
            date = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

            # Create a temporary list file
            temp_list_path = (
                get_list_path() / f"{self._application_name}-{version}-{date}-temp.yml"
            )
            list_path = (
                get_list_path() / f"{self._application_name}-{version}-{date}-list.yml"
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

    def clean_all(
        self,
        lock_created: Optional[bool] = None,
    ) -> Dict:
        """Clean all environments of a given package.

        Environments will be removed using conda/mamba, or the folders deleted in
        case conda fails.

        Parameters
        ----------
        package_name : str
            Name of the package.
        """
        # Try to remove shortcuts

        # Remove any broken envs
        for prefix in get_broken_envs(self._application_name):
            shutil.rmtree(prefix, ignore_errors=True)

        # TODO: Remove all data from the constructor manager config

        # TODO: Remove all the temp states and list files
        # napari-0.4.17-2023-02-22-18-35-34-temp.yml

        # Add actions taken by the clean all command
        return {}

    def uninstall(
        self,
        lock_created: Optional[bool] = None,
    ) -> Dict:
        """Uninstall the bundle application."""
        # Remove all shortcuts

        # Remove all the application environments

        # Remove the constructor environment

        # Remove the base environment

        # Remove everything else with rm rf $CONDA_PREFIX

    def open(
        self,
        version: str = None,
        target_prefix: str = None,
        lock_created: Optional[bool] = None,
    ) -> Dict:
        """Open the application with package name and version."""
        version = version if version else self._current_version
        exit_code = open_application(
            self._application_name, version, target_prefix=target_prefix
        )
        return {"exit_code": exit_code}
