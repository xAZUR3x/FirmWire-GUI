import signal
import threading
from queue import Queue
from subprocess import PIPE, STDOUT, Popen
from sys import executable as python_exe


class FirmWireRunner:
    def __init__(self):
        self.process = None
        self.reader_thread = None
        self._output_queue = Queue()

    def _read_process_output(self):
        if self.process is None or self.process.stdout is None:
            return

        for line in iter(self.process.stdout.readline, ""):
            self._output_queue.put(line.rstrip("\n"))

        self.process.stdout.close()

    def start(self, script_path, url):
        if self.process is not None and self.process.poll() is None:
            return False

        self._output_queue.queue.clear()

        self.process = Popen(
            [python_exe, str(script_path), url],
            cwd=script_path.parent,
            stdout=PIPE,
            stderr=STDOUT,
            text=True,
            bufsize=1,
        )

        self.reader_thread = threading.Thread(
            target=self._read_process_output,
            daemon=True,
        )
        self.reader_thread.start()
        return True

    def stop(self):
        if self.process is None or self.process.poll() is not None:
            return False

        self.process.send_signal(signal.SIGINT)
        return True

    def drain_output(self):
        output = []
        while not self._output_queue.empty():
            output.append(self._output_queue.get_nowait())
        return output

    def is_running(self):
        return self.process is not None and self.process.poll() is None
