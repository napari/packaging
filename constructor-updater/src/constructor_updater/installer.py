import contextlib
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Deque, Dict, List, Optional, Sequence, Tuple

from constructor_updater.defaults import DEFAULT_CHANNEL

job_id = int


class AbstractInstaller:
    """Abstract base class for package installers (pip, conda, etc)."""

    # abstract method
    def _modify_env(self, env: dict):
        raise NotImplementedError()

    # abstract method
    def _get_install_args(
        self, pkg_list: Sequence[str], prefix: Optional[str] = None
    ) -> Tuple[str, ...]:
        raise NotImplementedError()

    # abstract method
    def _get_uninstall_args(
        self, pkg_list: Sequence[str], prefix: Optional[str] = None
    ) -> Tuple[str, ...]:
        raise NotImplementedError()

    def __init__(self) -> None:
        super().__init__()
        self._processes = {}  # type: Dict[job_id, subprocess.Popen]
        self._bin = None  # type: Optional[str]
        env = os.environ.copy()
        env = self._modify_env(env)
        self._env = env
        self._queue: Deque[Tuple[str, ...]] = Deque()
        self._messages = []  # type: List[str]
        self._exit_codes = {}  # type: Dict[job_id, int]

    # -------------------------- Public API ------------------------------
    def install(
        self, pkg_list: Sequence[str], *, prefix: Optional[str] = None
    ) -> job_id:
        """Install packages in `pkg_list` into `prefix`.

        Parameters
        ----------
        pkg_list : Sequence[str]
            List of packages to install.
        prefix : Optional[str], optional
            Optional prefix to install packages into.

        Returns
        -------
        job_id : int
            ID that can be used to cancel the process.
        """
        return self._queue_args(self._get_install_args(pkg_list, prefix))

    def uninstall(
        self, pkg_list: Sequence[str], *, prefix: Optional[str] = None
    ) -> job_id:
        """Uninstall packages in `pkg_list` from `prefix`.

        Parameters
        ----------
        pkg_list : Sequence[str]
            List of packages to uninstall.
        prefix : Optional[str], optional
            Optional prefix from which to uninstall packages.

        Returns
        -------
        job_id : int
            ID that can be used to cancel the process.
        """
        return self._queue_args(self._get_uninstall_args(pkg_list))

    def cancel(self, job_id: Optional[job_id] = None):
        """Cancel `job_id` if it is running.

        Parameters
        ----------
        job_id : Optional[job_id], optional
            Job ID to cancel.  If not provided, cancel all jobs.
        """
        if job_id is None:
            # cancel all jobs
            self._queue.clear()
            for _job_id, process in self._processes.items():
                process.kill()
            return

        for i, args in enumerate(self._queue):
            if hash(args) == job_id:
                self._queue.remove(args)
                return

        raise ValueError(f"No job with id {job_id}")  # pragma: no cover

    # -------------------------- Private methods ------------------------------
    def _queue_args(self, args) -> job_id:
        args = (self._bin,) + args
        print(" ".join(args))
        self._queue.append(args)
        self._process_queue()
        return hash(args)

    def _process_queue(self):
        if not self._queue:
            return

        args = self._queue[0]
        job_id = hash(args)
        logging.debug("Starting %s %s", self._bin, args)

        popen = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=self._env,
        )
        self._processes[job_id] = popen

        for line in popen.stdout:
            self._on_output(line)
            # print(line, end='')

        for line in popen.stderr:
            self._on_output(line)
            # print(line, end='')

        popen.stdout.close()
        popen.stderr.close()
        return_code = popen.wait()
        self._on_process_finished(job_id, return_code, 0)

    def _on_output(self, line):
        # TODO: Write to file for logging and querying status
        print(line, end="")
        self._messages.append(line)

    def _on_process_finished(self, job_id: job_id, exit_code: int, exit_status: int):
        self._exit_codes[job_id] = exit_code
        with contextlib.suppress(IndexError):
            self._queue.popleft()

        logging.debug(
            "Finished with exit code %s and status %s. Output:\n%s",
            exit_code,
            exit_status,
        )
        self._process_queue()


class CondaInstaller(AbstractInstaller):
    """Conda installer."""

    def __init__(
        self, use_mamba: bool = True, pinned=None, channel=DEFAULT_CHANNEL
    ) -> None:
        self._bin = "mamba" if use_mamba and shutil.which("mamba") else "conda"
        self._pinned = pinned
        self._channels = (channel,)
        super().__init__()
        self._default_prefix = (
            sys.prefix if (Path(sys.prefix) / "conda-meta").is_dir() else None
        )

    def _modify_env(self, env: dict):
        if self._bin != "mamba":
            return

        PINNED = "CONDA_PINNED_PACKAGES"
        system_pins = f"&{env[PINNED]}" if PINNED in env else ""
        env[PINNED] = f"{self._pinned}{system_pins}"

        if os.name == "nt":
            if "TEMP" not in env:
                temp = tempfile.gettempdir()
                env["TMP"] = temp
                env["TEMP"] = temp

            if "USERPROFILE" not in env:
                env["HOME"] = os.path.expanduser("~")
                env["USERPROFILE"] = os.path.expanduser("~")

    def _get_create_args(
        self, pkg_list: Sequence[str], prefix: Optional[str] = None
    ) -> Tuple[str, ...]:
        return self._get_args("create", pkg_list, prefix)

    def _get_remove_args(self, prefix: str) -> Tuple[str, ...]:
        return self._get_args("remove", ["--all"], prefix)

    def _get_install_args(
        self, pkg_list: Sequence[str], prefix: Optional[str] = None
    ) -> Tuple[str, ...]:
        return self._get_args("install", pkg_list, prefix)

    def _get_uninstall_args(
        self, pkg_list: Sequence[str], prefix: Optional[str] = None
    ) -> Tuple[str, ...]:
        return self._get_args("remove", pkg_list, prefix)

    def _get_args(self, arg0, pkg_list: Sequence[str], prefix: Optional[str]):
        cmd = [arg0, "-yq"]
        if prefix := str(prefix or self._default_prefix):
            cmd.extend(["--prefix", prefix])

        for channel in self._channels:
            cmd.extend(["-c", channel])

        return tuple(cmd + list(pkg_list))

    # -------------------------- Public API ----------------------------------
    def create(
        self, pkg_list: Sequence[str], *, prefix: Optional[str] = None
    ) -> job_id:
        return self._queue_args(self._get_create_args(pkg_list, prefix))

    def install(
        self, pkg_list: Sequence[str], *, prefix: Optional[str] = None
    ) -> job_id:
        """Install packages in `pkg_list` into `prefix`.

        Parameters
        ----------
        pkg_list : Sequence[str]
            List of packages to install.
        prefix : Optional[str], optional
            Optional prefix to install packages into.

        Returns
        -------
        job_id : int
            ID that can be used to cancel the process.
        """
        return self._queue_args(self._get_install_args(pkg_list, prefix=prefix))

    def uninstall(
        self, pkg_list: Sequence[str], *, prefix: Optional[str] = None
    ) -> job_id:
        """Uninstall packages in `pkg_list` from `prefix`.

        Parameters
        ----------
        pkg_list : Sequence[str]
            List of packages to uninstall.
        prefix : Optional[str], optional
            Optional prefix from which to uninstall packages.

        Returns
        -------
        job_id : int
            ID that can be used to cancel the process.
        """
        return self._queue_args(self._get_uninstall_args(pkg_list, prefix=prefix))

    def remove(self, prefix) -> job_id:
        """"""
        return self._queue_args(self._get_remove_args(prefix))
