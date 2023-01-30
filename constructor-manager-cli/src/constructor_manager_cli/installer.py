import contextlib
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Sequence, Tuple, cast

from constructor_manager_cli.defaults import DEFAULT_CHANNEL

job_id = int


class AbstractInstaller:
    """Abstract base class for package installers (pip, conda, etc)."""

    # abstract method
    def _modify_env(self, env: Dict):
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
        self._messages: List[str] = []
        self._exit_codes: Dict[job_id, int] = {}

    # -------------------------- Public API ------------------------------
    def install(
        self,
        pkg_list: Sequence[str],
        *,
        prefix: Optional[str] = None,
        block: bool = False,
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
    def _queue_args(self, args, bin=None, block=False) -> job_id:
        if bin:
            args = (bin,) + tuple(args) + (block,)
        else:
            args = (self._bin,) + tuple(args) + (block,)

        self._queue.append(args)
        res = self._process_queue()
        if res:
            return res
        else:
            return hash(args[:-1])  # Do not include the last block parameter in hash

    def _process_queue(self):
        if not self._queue:
            return

        args = self._queue[0][:-1]
        block = self._queue[0][-1]
        # Do not include the last block parameter in hash
        job_id = hash(args)
        logging.debug("Starting %s %s", self._bin, args)
        # print("ÄRGS", ' '.join(args))

        popen = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=self._env,
        )
        self._processes[job_id] = popen
        if block:
            stdout, stderr = popen.communicate()

            if isinstance(stdout, bytes):
                stdout = stdout.decode()

            if isinstance(stderr, bytes):
                stderr = stderr.decode()

            # TODO: Write to file for logging and querying status
            return_code = popen.returncode
            self._on_process_finished(job_id, return_code, 0)
            try:
                res = json.loads(stdout)
            except json.JSONDecodeError:
                res = {"stdout": stdout}
            return res
        else:
            # for line in popen.stdout:
            #     self._on_output(line)
            #     # print(line, end='')

            # for line in popen.stderr:
            #     self._on_output(line)
            #     # print(line, end='')

            # popen.stdout.close()
            # popen.stderr.close()
            # return_code = popen.wait()

            while True:
                output = popen.stdout.readline()
                if isinstance(output, bytes):
                    output = output.decode()

                if output == "" and popen.poll() is not None:
                    break

                return_code = popen.poll()

            self._on_process_finished(job_id, return_code, 0)

    def _on_output(self, line):
        # TODO: Write to file for logging and querying status
        print(line, end="")
        self._messages.append(line)

    def _on_process_finished(
        self,
        job_id: job_id,
        exit_code: int,
        exit_status: int,
    ):
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
        self, use_mamba: bool = True, pinned=None, channels=(DEFAULT_CHANNEL,)
    ) -> None:
        self._pinned = pinned
        self._channels = channels
        super().__init__()
        self._bin = "mamba" if use_mamba and shutil.which("mamba") else "conda"
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
        cmd = [arg0, "-y"]
        if prefix := str(prefix or self._default_prefix):
            cmd.extend(["--prefix", prefix])

        for channel in self._channels:
            cmd.extend(["-c", channel])

        if pkg_list:
            cmd.extend(pkg_list)

        return tuple(cmd)

    # -------------------------- Public API ----------------------------------
    def info(self) -> Dict[Any, Any]:
        """Get conda info."""
        args = ["info", "--json"]
        res = cast(dict, self._queue_args(args, block=True))
        return res

    def list(self, prefix: str, block=False) -> job_id:
        """List packages for `prefix`.

        Parameters
        ----------
        prefix : str
            Prefix from which to list packages.

        Returns
        -------
        job_id : int
            ID that can be used to cancel the process.
        """
        return self._queue_args(
            ("list", "--prefix", str(prefix), "--json"), block=block
        )

    def install_from_lock(
        self,
        prefix: str,
        lockfile: str,
        block: bool = False,
    ) -> job_id:
        """Install packages from lockfile."""
        args = ["-p", prefix, "--lockfile", lockfile]
        return self._queue_args(args, bin="conda-lock", block=block)

    def lock(
        self,
        env_path: str,
        lockfile: Optional[str] = None,
        block: bool = False,
    ) -> job_id:
        """List packages for `prefix`.

        Parameters
        ----------
        prefix : str
            Prefix from which to list packages.

        Returns
        -------
        job_id : int
            ID that can be used to cancel the process.
        """
        args = ["-f", env_path]
        if lockfile:
            args.extend(["--lockfile", lockfile])

        return self._queue_args(args, bin="conda-lock", block=block)

    def create(
        self, prefix: str, *, pkg_list: Sequence[str] = (), block: bool = False
    ) -> job_id:
        """Create a new conda environment with `pkg_list` in `prefix`.

        Parameters
        ----------
        pkg_list : Sequence[str]
            List of packages to install on new environment.
        prefix : str, optional
            Optional prefix for new environment.

        Returns
        -------
        job_id : int
            ID that can be used to cancel the process.
        """
        return self._queue_args(self._get_create_args(pkg_list, prefix), block=block)

    def remove(self, prefix: str, block: bool = False) -> job_id:
        """Remove a conda environment in `prefix`.

        Parameters
        ----------
        prefix : str, optional
            Optional prefix for new environment.

        Returns
        -------
        job_id : int
            ID that can be used to cancel the process.
        """
        return self._queue_args(self._get_remove_args(prefix), block=block)

    def install(
        self,
        prefix: Optional[str],
        pkg_list: Sequence[str],
        shortcuts: bool = False,
        block: bool = False,
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
        return self._queue_args(self._get_install_args(pkg_list, prefix), block=block)

    def uninstall(
        self,
        pkg_list: Sequence[str],
        *,
        prefix: Optional[str] = None,
        shortcuts: bool = False,
        block: bool = False,
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
        return self._queue_args(self._get_uninstall_args(pkg_list, prefix), block=block)
