import re
import shutil
import subprocess
import os
import platform
import sys
import uuid
from pathlib import Path

from flask import Flask, jsonify, send_file
from check_devices import linux_printers, system_bitness, windows_printers


ROOT = Path(__file__).resolve().parent


def app_data_directory():
    if not getattr(sys, "frozen", False):
        return ROOT
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Scan2scanner"
    data_home = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(data_home) / "scan2scanner"


SCAN_DIRECTORY = app_data_directory() / "scans"
app = Flask(__name__)


def list_windows_scanners():
    try:
        import win32com.client
    except ImportError:
        return None, "Install the Windows requirements from requirements.txt."

    try:
        manager = win32com.client.Dispatch("WIA.DeviceManager")
        scanners = []
        for index in range(1, manager.DeviceInfos.Count + 1):
            device_info = manager.DeviceInfos.Item(index)
            if device_info.Type != 1:
                continue
            scanners.append(
                {
                    "id": str(device_info.DeviceID),
                    "name": str(device_info.Properties("Name").Value),
                }
            )
        return scanners, None
    except Exception as error:
        return None, f"Windows could not query WIA scanners: {error}"


def list_scanners():
    if os.name == "nt":
        return list_windows_scanners()

    scanimage = shutil.which("scanimage")
    if not scanimage:
        return None, "SANE is not installed. Install the sane-utils package."

    result = subprocess.run(
        [scanimage, "-L"], capture_output=True, text=True, timeout=15, check=False
    )
    output = f"{result.stdout}\n{result.stderr}"
    scanners = []
    for device, description in re.findall(
        r"device `([^']+)' is a (.+)", output
    ):
        scanners.append({"id": device, "name": description.strip()})
    return scanners, None


def scan_windows(device_id, output_path):
    import win32com.client

    manager = win32com.client.Dispatch("WIA.DeviceManager")
    for index in range(1, manager.DeviceInfos.Count + 1):
        device_info = manager.DeviceInfos.Item(index)
        if str(device_info.DeviceID) == device_id:
            device = device_info.Connect()
            scan_item = device.Items.Item(1)
            resolution = set_wia_resolution(scan_item)
            image = scan_item.Transfer(
                "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}"
            )
            image.SaveFile(str(output_path))
            return resolution
    raise RuntimeError("The selected scanner is no longer available.")


def set_wia_resolution(scan_item):
    for resolution in (600, 300):
        try:
            scan_item.Properties("6147").Value = resolution
            scan_item.Properties("6148").Value = resolution
            return resolution
        except Exception:
            continue
    return None


def supported_sane_resolution(scanimage, device_id):
    try:
        result = subprocess.run(
            [scanimage, "--all-options", "--device-name", device_id],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    match = re.search(r"^\s*--resolution(?:=|\s+)([^\r\n]+)", result.stdout, re.MULTILINE)
    if not match:
        return None
    options = match.group(1).split("[", 1)[0]
    resolutions = [int(value) for value in re.findall(r"\d+", options)]
    if not resolutions:
        return None
    up_to_600 = [value for value in resolutions if 75 <= value <= 600]
    return max(up_to_600) if up_to_600 else min(resolutions)


@app.get("/")
def index():
    return send_file(ROOT / "index.html")


@app.get("/styles.css")
def styles():
    return send_file(ROOT / "styles.css", mimetype="text/css")


@app.get("/app.js")
def script():
    return send_file(ROOT / "app.js", mimetype="text/javascript")


@app.get("/api/scanners")
def scanners():
    devices, error = list_scanners()
    if error:
        return jsonify(error=error, scanners=[]), 503
    return jsonify(scanners=devices)


@app.get("/api/system-info")
def system_info():
    if os.name == "nt":
        version = platform.win32_ver()[0]
        os_name = f"Windows {version}" if version else "Windows"
        printers, printer_error = windows_printers()
        scanner_interface = "WIA"
    elif sys.platform.startswith("linux"):
        os_name = "Linux"
        printers, printer_error = linux_printers()
        scanner_interface = "SANE"
    else:
        os_name = platform.system()
        printers, printer_error = [], "نظام التشغيل غير مدعوم لفحص الطابعات."
        scanner_interface = "غير معروف"

    return jsonify(
        os_name=os_name,
        os_bitness=system_bitness(),
        architecture=platform.machine(),
        python_bitness="64-bit" if sys.maxsize > 2**32 else "32-bit",
        scanner_interface=scanner_interface,
        printers=[
            {"name": name, "state": state, "details": details}
            for name, state, details in printers
        ],
        printer_error=printer_error,
    )


@app.post("/scan/")
def scan():
    devices, error = list_scanners()
    if error:
        return jsonify(error=error), 503
    if not devices:
        return jsonify(error="لم يتم العثور على ماسح ضوئي. تحقق من كابل USB ودعم SANE."), 503

    SCAN_DIRECTORY.mkdir(exist_ok=True)
    filename = f"scan-{uuid.uuid4().hex}.png"
    output_path = SCAN_DIRECTORY / filename
    resolution = None
    if os.name == "nt":
        try:
            resolution = scan_windows(devices[0]["id"], output_path)
        except Exception as error:
            output_path.unlink(missing_ok=True)
            return jsonify(error=f"Windows scan failed: {error}"), 502
    else:
        scanimage = shutil.which("scanimage")
        resolution = supported_sane_resolution(scanimage, devices[0]["id"])
        command = [
            scanimage,
            "--device-name",
            devices[0]["id"],
            "--format=png",
            f"--output-file={output_path}",
        ]
        if resolution:
            command.append(f"--resolution={resolution}")
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return jsonify(error="انتهت مهلة المسح. تحقق من الماسح وحاول مجدداً."), 504

        if result.returncode != 0 or not output_path.is_file() or output_path.stat().st_size == 0:
            output_path.unlink(missing_ok=True)
            message = result.stderr.strip() or "فشل الماسح في إكمال العملية."
            return jsonify(error=message), 502

    return jsonify(
        filename=filename,
        image_url=f"/scans/{filename}",
        resolution_dpi=resolution,
    )


@app.get("/scans/<filename>")
def scanned_image(filename):
    if not re.fullmatch(r"scan-[a-f0-9]{32}\.png", filename):
        return jsonify(error="صورة غير صالحة."), 404
    path = SCAN_DIRECTORY / filename
    if not path.is_file():
        return jsonify(error="الصورة غير موجودة."), 404
    return send_file(path, mimetype="image/png", as_attachment=False)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)