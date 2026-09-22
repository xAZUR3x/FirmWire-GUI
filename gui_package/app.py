import logging
import shutil
import tempfile
from pathlib import Path
from nicegui import app, ui
from .app_logic import FirmWireAppLogic

URL = (
    "https://github.com/grant-h/ShannonFirmware/raw/master/modem_files/"
    "CP_G973FXXU3ASG8_CP13372649_CL16487963_QB24948473_REV01_user_low_ship.tar.md5.lz4"
)

fw_app_logic = FirmWireAppLogic()
script_path = Path(__file__).resolve().parent.parent / "firmwire" / "firmwire.py"
modem_source = URL
uploaded_modem_path = None


class LogViewHandler(logging.Handler):
    def __init__(self, log_view):
        super().__init__()
        self._log_view = log_view

    def emit(self, record):
        try:
            msg = self.format(record)
            parsed_log = fw_app_logic.parse_logs([msg])
            if parsed_log:
                self._log_view.push(msg)
        except Exception:
            self.handleError(record)

class LogTableHandler(logging.Handler):
    def __init__(self, log_table):
        super().__init__()
        self._log_table = log_table

    def emit(self, record):
        try:
            msg = self.format(record)
            parsed_log = fw_app_logic.parse_logs([msg])
            if parsed_log:
                parsed_log = parsed_log[0]
                self._log_table.rows.append({
                    'time': parsed_log.time,
                    'task': parsed_log.task,
                    'address_symbol': parsed_log.address_symbol,
                    'bitmask': parsed_log.bitmask or '',
                    'source': parsed_log.source or '',
                    'message': parsed_log.message or '',
                })
                self._log_table.update()
        except Exception:
            self.handleError(record)

def attach_handlers(log_view, log_table):
    log_view_handler = LogViewHandler(log_view)
    log_table_handler = LogTableHandler(log_table)

    logger = fw_app_logic.get_logger()
    logger.addHandler(log_view_handler)
    logger.addHandler(log_table_handler)

def build_ui():
    global status_label, line_count_label, log_view, log_table
    global task_filter_input, address_symbol_filter_input
    global bitmask_filter_input, time_filter_min_input, time_filter_max_input
    global modem_mode, modem_url_input, modem_upload, modem_source_label

    with ui.tabs().classes("w-full") as tabs:
        ui.tab("runner", label="Runner")
    
    with ui.tab_panels(tabs, value="runner").classes("w-full"):
        with ui.tab_panel("runner"):
            with ui.row().classes("items-stretch gap-20"):
                with ui.column().classes("items-center justify-center gap-2"):
                    ui.label("Runner Controls").classes("text-h6")
                    with ui.row().classes("items-center gap-2"):
                        ui.button("Start", on_click=start_firmwire)
                        ui.button("Stop", on_click=stop_firmwire)
                        ui.button("Exit", on_click=lambda: (app.shutdown(), ui.notify("Closing UI...")))
                    
                    status_label = ui.label("Status: Stopped").classes("text-h6")
                    line_count_label = ui.label(f"Log Lines: 0").classes("text-h6")

                ui.separator().props("vertical")
                
                with ui.column().classes("items-left gap-2"):
                    ui.label("Filters").classes("text-h6")
                    with ui.row().classes("items-center gap-2"):
                        ui.label("Task:")
                        task_filter_input = ui.input(placeholder="Filter by Task")
                    with ui.row().classes("items-center gap-2"):
                        ui.label("Address/Symbol:")
                        address_symbol_filter_input = ui.input(placeholder="Filter by Address/Symbol")
                    with ui.row().classes("items-center gap-2"):
                        ui.label("Bitmask:")
                        bitmask_filter_input = ui.input(placeholder="Filter by Bitmask")
                    with ui.row().classes("items-center gap-2"):
                        ui.label("Time Range:")
                        time_filter_min_input = ui.input(placeholder="Min Time")
                        time_filter_max_input = ui.input(placeholder="Max Time")
                    ui.button("Filter", on_click=apply_filters)

                ui.separator().props("vertical")

                with ui.column().classes("items-left gap-2"):
                    ui.label("Export Logs").classes("text-h6")
                    ui.button("Export", on_click=lambda: export_logs(log_view))
                    ui.label("Modem").classes("text-h6")
                    modem_mode = ui.radio(
                        {"url": "URL", "upload": "Upload"},
                        value="url",
                        on_change=lambda e: set_modem_mode())
                    modem_url_input = ui.input(
                        placeholder="Enter Modem URL",
                        value=URL,
                        on_change=set_modem_source,
                    ).classes("w-96")
                    modem_upload = ui.upload(
                        label="Upload Modem File",
                        auto_upload=True,
                        on_upload=handle_modem_upload,
                    )
                    modem_source_label = ui.label(f"Source: {modem_source}").classes("text-caption").style(
                        "max-width: 24rem; overflow-wrap: anywhere;"
                    )
                    set_modem_mode()

            with ui.tabs().classes("w-full") as tabs:
                ui.tab("raw", label="Raw Output")
                ui.tab("table", label="Table View")

            with ui.tab_panels(tabs, value="raw").classes("w-full"):
                with ui.tab_panel("raw"):
                    log_view = ui.log()
                    log_view.classes("whitespace-pre-wrap")
                    log_view.style(
                        "display: block; width: 100%; min-height: 600px; background-color: #f3f4f6; overflow: auto; padding: 0.75rem; border-radius: 0.375rem;"
                    )

                with ui.tab_panel("table"):
                    log_table = ui.table(
                        columns=[
                            {'name': 'time', 'label': 'Time', 'field': 'time'},
                            {'name': 'task', 'label': 'Task', 'field': 'task'},
                            {'name': 'address_symbol', 'label': 'Address/Symbol', 'field': 'address_symbol'},
                            {'name': 'bitmask', 'label': 'Bitmask', 'field': 'bitmask'},
                            {'name': 'source', 'label': 'Source', 'field': 'source'},
                            {'name': 'message', 'label': 'Message', 'field': 'message'},
                        ],
                        rows=[]
                    ).style("width: 100%; height: 600px;")
                
                attach_handlers(log_view, log_table)

    app.on_shutdown(fw_app_logic.stop)
    ui.timer(interval=0.1, callback=update_status)


def start_firmwire():
    if not modem_source:
        ui.notify("Choose a modem file or enter a modem URL", type="negative")
        return

    if not fw_app_logic.start(script_path, modem_source):
        ui.notify("FirmWire is already running")
        return

    log_view.clear()
    log_table.rows.clear()
    log_table.update()
    fw_app_logic.reset_output()
    ui.notify("Starting FirmWire...")
    update_status()


def stop_firmwire():
    if not fw_app_logic.stop():
        ui.notify("FirmWire is not running")
        return

    ui.notify("Stopping FirmWire...")
    update_status()


def update_status():
    if "status_label" not in globals() or "line_count_label" not in globals() or "log_view" not in globals():
        return

    status_label.set_text(f"Status: {'Running' if fw_app_logic.is_running() else 'Stopped'}")
    line_count_label.set_text(f"Log Lines: {fw_app_logic.get_line_count()}")


def apply_filters():
    fw_app_logic.set_task_filter(task_filter_input.value)
    fw_app_logic.set_address_symbol_filter(address_symbol_filter_input.value)
    fw_app_logic.set_bitmask_filter(bitmask_filter_input.value)
    fw_app_logic.set_time_filter(
        minimum=time_filter_min_input.value,
        maximum=time_filter_max_input.value,
    )
    filter_logs(log_view, log_table)


def filter_logs(log_view, log_table):
    log_view.clear()
    log_table.rows.clear()
    for log in fw_app_logic.get_full_logs():
        parsed_logs = fw_app_logic.parse_logs([log])
        if not parsed_logs:
            continue

        parsed_log = parsed_logs[0]
        log_view.push(log)
        log_table.rows.append({
            'time': parsed_log.time,
            'task': parsed_log.task,
            'address_symbol': parsed_log.address_symbol,
            'bitmask': parsed_log.bitmask or '',
            'source': parsed_log.source or '',
            'message': parsed_log.message or '',
        })

    log_table.update()

def export_logs(log_view):
    logs = []
    for log in fw_app_logic.get_full_logs():
        parsed_logs = fw_app_logic.parse_logs([log])
        if not parsed_logs:
            continue
        logs.append(log)

    log_text = "\n".join(logs)
    ui.download(log_text.encode("utf-8"), "firmwire_logs.txt", media_type="text/plain")

def set_modem_mode():
    modem_url_input.set_visibility(modem_mode.value == "url")
    modem_upload.set_visibility(modem_mode.value == "upload")

    if modem_mode.value == "url":
        set_modem_source(modem_url_input.value)
    elif uploaded_modem_path:
        set_modem_source(uploaded_modem_path)
    else:
        set_modem_source(None)


def set_modem_source(source):
    global modem_source

    modem_source = source
    modem_source_label.set_text(f"Source: {modem_source or 'None'}")

def handle_modem_upload(event):
    global modem_source, uploaded_modem_path

    upload_dir = Path(tempfile.gettempdir()) / "firmwire-gui"
    upload_dir.mkdir(parents=True, exist_ok=True)
    uploaded_modem_path = upload_dir / Path(event.name).name
    with uploaded_modem_path.open("wb") as destination:
        shutil.copyfileobj(event.content, destination)

    set_modem_source(uploaded_modem_path)
    ui.notify(f"Loaded modem file: {event.name}")

def main():
    build_ui()
    ui.run(title="FirmWire GUI", host="0.0.0.0", port=8080)