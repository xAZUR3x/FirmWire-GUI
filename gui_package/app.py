from pathlib import Path
from nicegui import app, ui
from .app_logic import FirmWireAppLogic

URL = (
    "https://github.com/grant-h/ShannonFirmware/raw/master/modem_files/"
    "CP_G973FXXU3ASG8_CP13372649_CL16487963_QB24948473_REV01_user_low_ship.tar.md5.lz4"
)

fw_app_logic = FirmWireAppLogic()
script_path = Path(__file__).resolve().parent.parent / "firmwire" / "firmwire.py"


def build_ui():
    global status_label, line_count_label, log_view
    
    with ui.column().classes("items-center gap-2"):
        ui.label("FirmWire GUI").classes("text-h4")
        status_label = ui.label("Status: Stopped").classes("text-h6")
        line_count_label = ui.label(f"Log Lines: 0").classes("text-h6")

        with ui.row().classes("items-center gap-2"):
            ui.button("Start", on_click=start_firmwire)
            ui.button("Stop", on_click=stop_firmwire)
            ui.button("Exit", on_click=lambda: (app.shutdown(), ui.notify("Closing UI..."))).classes("bg-red-500 text-white")

    log_view = ui.textarea(value="", placeholder="Logs will appear here...").style("width: 100%; height: 600px;")

    app.on_shutdown(fw_app_logic.stop)
    ui.timer(interval=0.1, callback=update_status)


def start_firmwire():
    if not fw_app_logic.start(script_path, URL):
        ui.notify("FirmWire is already running")
        return

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

    status_label.set_text(f"Status: {fw_app_logic.get_status()}")
    line_count_label.set_text(f"Log Lines: {fw_app_logic.get_line_count()}")
    log_view.set_value("\n".join(fw_app_logic.ui_output()))


def main():
    build_ui()
    ui.run(title="FirmWire GUI", host="0.0.0.0", port=8080)
