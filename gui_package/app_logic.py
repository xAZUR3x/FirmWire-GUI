import logging
from .runner import FirmWireRunner
from dataclasses import dataclass
from typing import Optional

@dataclass
class LogEntry:
    time: float
    task: str
    address_symbol: str

    bitmask: Optional[str] = None
    source: Optional[str] = None
    message: Optional[str] = None


class FirmWireAppLogic:
    def __init__(self):
        self._runner = FirmWireRunner()
        self._time_filter = (None, None)
        self._task_filter = []
        self._address_symbol_filter = []
        self._bitmask_filter = []

    def set_time_filter(self, minimum=None, maximum=None):
        if minimum is not None:
            try:
                minimum = float(minimum)
            except ValueError:
                minimum = None
        if maximum is not None:
            try:
                maximum = float(maximum)
            except ValueError:
                maximum = None
        self._time_filter = (minimum, maximum)

    def set_task_filter(self, tasks):
        self._task_filter = tasks

    def set_address_symbol_filter(self, address_symbols):
        self._address_symbol_filter = address_symbols

    def set_bitmask_filter(self, bitmasks):
        self._bitmask_filter = bitmasks

    def start(self, script_path, url):
        return self._runner.start(script_path, url)

    def stop(self):
        return self._runner.stop()

    def get_full_logs(self):
        return self._runner.get_full_logs()
    
    def get_logger(self):
        return self._runner.get_logger()
    
    def reset_output(self):
        self._runner.reset_output()

    def is_running(self):
        return self._runner.is_running()

    def get_line_count(self):
        return str(len(self._runner.get_full_logs()))

    def parse_logs(self, logs=None):
        if logs is None:
            logs = self._runner.get_full_logs()
        parsed_logs = []
        n = len(logs)
        while n > 0:
            bitmask = None
            source = None
            message = None

            line = logs[n - 1]
            if not line.startswith("[") and not line.startswith(".["):
                n -= 1
                continue

            first_open = line.find("[")
            first_close = line.find("]")
            try:
                time = float(line[first_open + 1:first_close])
            except ValueError:
                n -= 1
                continue
            second_close = line.find("]", first_close + 1)
            if second_close == -1:
                n -= 1
                continue
            task = line[first_close + 2:second_close]

            try:
                line = line[second_close + 2:]
                line_parts = line.split(" ")

                address_symbol = line_parts[0]
                if line_parts[1].startswith("("):
                    line_parts.pop(1)
                if line_parts[1].startswith("0b"):
                    bitmask = line_parts[1][:-1]
                    source = line_parts[2]
                    message = " ".join(line_parts[3:])
                elif line_parts[1].startswith("["):
                    source = line_parts[1]
                    message = " ".join(line_parts[2:])
                else:
                    message = " ".join(line_parts[1:])
            except:
                n -= 1
                continue

            minimum_time, maximum_time = self._time_filter
            if minimum_time:
                if time < minimum_time:
                    n -= 1
                    continue
            if maximum_time:
                if time > maximum_time:
                    n -= 1
                    continue
            if self._task_filter:
                if task not in self._task_filter:
                    n -= 1
                    continue
            if self._address_symbol_filter:
                if address_symbol not in self._address_symbol_filter:
                    n -= 1
                    continue
            if self._bitmask_filter:
                if bitmask is None:
                    n -= 1
                    continue
                if bitmask not in self._bitmask_filter:
                    n -= 1
                    continue

            parsed_logs.append(LogEntry(time=time, task=task, address_symbol=address_symbol, bitmask=bitmask, source=source, message=message))
            n -= 1
        return parsed_logs