from .runner import FirmWireRunner


class FirmWireAppLogic:
    def __init__(self, runner=None):
        self.runner = runner or FirmWireRunner()
        self._log_lines = []

    def start(self, script_path, url):
        started = self.runner.start(script_path, url)
        if started:
            self._log_lines = []
        return started

    def stop(self):
        return self.runner.stop()

    def drain_output(self):
        new_lines = self.runner.drain_output()
        if new_lines:
            self._log_lines.extend(new_lines)
            if len(self._log_lines) > 300:
                self._log_lines = self._log_lines[-300:]
        return new_lines

    def is_running(self):
        return self.runner.is_running()

    def get_status(self):
        return "Running" if self.is_running() else "Stopped"

    def get_line_count(self):
        return len(self._log_lines)

    def get_log_lines(self):
        return self._log_lines
