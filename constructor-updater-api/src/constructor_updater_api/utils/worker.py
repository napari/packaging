"""Constructor updater api worker."""

import json

from constructor_updater_api.utils.conda import get_base_prefix
from qtpy.QtCore import QObject, QProcess, Signal


class ContructorUpdaterWorker(QObject):
    """TODO:

    Parameters
    ----------
    args : list
        Arguments to pass to the constructor updater.
    detached : bool, optional
        Run the process detached, by default ``False``.
    """

    finished = Signal(dict)

    def __init__(self, args, detached=False):
        super().__init__()
        self._detached = detached
        self._program = get_base_prefix() / "bin" / "constructor-updater"

        if not self._program.is_file():
            raise FileNotFoundError(f"Could not find {self._program}")

        self._process = QProcess()
        self._process.setArguments(args)
        self._process.setProgram(str(self._program))
        self._process.finished.connect(self._finished)

    def _finished(self, *args, **kwargs):
        """Handle the finished signal of the worker and emit results."""
        stdout = self._process.readAllStandardOutput()
        stderr = self._process.readAllStandardError()
        data = stdout.data().decode()
        error = stderr.data().decode()
        try:
            data = json.loads(data)
        except Exception as e:
            print(e)

        result = {"data": data, "error": error}
        self.finished.emit(result)

    def start(self):
        """Start the worker."""
        if self._detached:
            self._process.startDetached()
        else:
            self._process.start()
