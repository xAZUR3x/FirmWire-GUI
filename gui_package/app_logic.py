from .runner import FirmWireRunner


class FirmWireAppLogic:
    def __init__(self):
        self._runner = FirmWireRunner()

    def start(self, script_path, url):
        return self._runner.start(script_path, url)

    def stop(self):
        return self._runner.stop()

    def ui_output(self):
        return self._runner.get_output()[-10000:]

    def is_running(self):
        return self._runner.is_running()

    def get_status(self):
        return "Running" if self.is_running() else "Stopped"

    def get_line_count(self):
        return str(len(self._runner.get_output())) + " (capped to 10000)" if len(self._runner.get_output()) > 10000 else str(len(self._runner.get_output()))
