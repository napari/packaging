"""Constructor updater api worker."""

import json
import logging

from qtpy.QtCore import QObject, QProcess, Signal  # type: ignore

from constructor_manager.utils.conda import get_base_prefix


logger = logging.getLogger(__name__)


class ConstructorManagerWorker(QObject):
    """A worker to run the constructor manager cli and process errors.

    Parameters
    ----------
    args : list
        Arguments to pass to the constructor manager.
    detached : bool, optional
        Run the process detached, by default ``False``.
    """

    _WORKERS: 'ConstructorManagerWorker' = []
    finished = Signal(dict)

    def __init__(self, args, detached=False):
        super().__init__()
        ConstructorManagerWorker._WORKERS.append(self)
        self._detached = detached
        self._program = get_base_prefix() / "bin" / "constructor-manager"

        if not self._program.is_file():
            raise FileNotFoundError(f"Could not find {self._program}")

        # TODO: Environemnt variables?
        self._args = args
        self._process = QProcess()
        self._process.setArguments(args)
        self._process.setProgram(str(self._program))
        self._process.finished.connect(self._finished)

    def _finished(self, exit_code: int, exit_status: QProcess.ExitStatus = QProcess.ExitStatus.NormalExit):
        """Handle the finished signal of the worker and emit results."""
        logger.debug("Worker with args `%s` finished with exit code %s and exit status %s", ' '.join(self._args), exit_code, exit_status)
        try:
            stdout = self._process.readAllStandardOutput()
            stderr = self._process.readAllStandardError()
        except RuntimeError as e:
            # TODO: Fix this?
            self.finished.emit({"data": {}, "error": str(e)})
            return

        # TODO: Ensure to have the proper propagation of issues
        raw_output = stdout.data().decode()
        raw_error = stderr.data().decode()
        error = raw_error

        output = {}
        if exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
            try:
                output = json.loads(raw_output)
            except Exception as e:
                error = raw_output

        data = output.get("data", raw_output)
        error = error or output.get("error", error)
        result = {"data": data, "error": error, "exit_code": exit_code, "exit_status": exit_status}
        self.finished.emit(result)

    def state(self):
        """State of the worker."""
        return self._process.state()

    def start(self):
        """Start the worker."""
        logger.debug("Worker with args `%s` started!", ' '.join(self._args))
        self._process.startDetached() if self._detached else self._process.start()

    def terminate(self):
        """Terminate the process worker."""
        logger.debug("Worker with args `%s` terminated!", ' '.join(self._args))
        self._process.terminate()
