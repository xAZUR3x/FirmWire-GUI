import signal
import threading
import logging
from subprocess import PIPE, STDOUT, Popen
from sys import executable as python_exe


class FirmWireRunner:
    def __init__(self):
        self._process = None
        self._reader_thread = None
        self._output = []
        self._logger = logging.getLogger(f"{__name__}.FirmWireRunner")
        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(logging.NullHandler())
        self._logger.propagate = False

    def _read_process_output(self):
        if self._process is None or self._process.stdout is None:
            return

        for line in iter(self._process.stdout.readline, ""):
            line_text = line.rstrip("\n")
            self._output.append(line_text)
            self._logger.info(line_text)

        self._process.stdout.close()

    def start(self, script_path, url):
        if self._process is not None and self._process.poll() is None:
            return False

        self._output = []

        self._process = Popen(
            [python_exe, str(script_path), url],
            cwd=script_path.parent,
            stdout=PIPE,
            stderr=STDOUT,
            text=True,
            bufsize=1,
        )

        self._reader_thread = threading.Thread(
            target=self._read_process_output,
            daemon=True,
        )
        self._reader_thread.start()
        return True

    def stop(self):
        if self._process is None or self._process.poll() is not None:
            return False

        self._process.send_signal(signal.SIGINT)
        return True

    def get_full_logs(self):
        return self._output
    
    def get_logger(self):
        return self._logger
    
    def reset_output(self):
        self._output = []

    def is_running(self):
        return self._process is not None and self._process.poll() is None
