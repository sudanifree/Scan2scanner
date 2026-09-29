import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import time


def run_command(command):
    try:
        return subprocess.run(
            command, capture_output=True, text=True, timeout=15, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return error


def system_bitness():
    if os.name == "nt":
        architecture = os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get(
            "PROCESSOR_ARCHITECTURE", ""
        )
        if architecture:
            return "64-bit" if architecture.lower().endswith("64") else "32-bit"

    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64", "aarch64", "arm64", "ppc64", "ppc64le", "s390x", "riscv64"}:
        return "64-bit"
    if machine in {"i386", "i486", "i586", "i686", "x86", "arm", "armv7l"}:
        return "32-bit"
    return "غير معروف"


def linux_scanners():
    scanimage = shutil.which("scanimage")
    if not scanimage:
        return [], "لم يتم العثور على scanimage. ثبّت حزمة sane-utils."

    result = run_command([scanimage, "-L"])
    if isinstance(result, Exception):
        return [], f"تعذر تشغيل فحص الماسح: {result}"

    scanners = [
        (
            name.strip(),
            "مكتشف عبر SANE",
            f"Backend: {device.split(':', 1)[0]} | Device: {device}",
        )
        for device, name in re.findall(r"device `([^']+)' is a (.+)", result.stdout)
    ]
    if result.returncode != 0:
        return scanners, result.stderr.strip() or "فشل فحص أجهزة SANE."
    return scanners, None


def windows_scanners():
    try:
        import win32com.client

        manager = win32com.client.Dispatch("WIA.DeviceManager")
        scanners = []
        for index in range(1, manager.DeviceInfos.Count + 1):
            device = manager.DeviceInfos.Item(index)
            if device.Type == 1:
                scanners.append(
                    (
                        str(device.Properties("Name").Value),
                        "مكتشف عبر WIA",
                        f"Device ID: {device.DeviceID}",
                    )
                )
        return scanners, None
    except ImportError:
        return [], "مكتبة pywin32 غير مثبتة. ثبّت متطلبات المشروع."
    except Exception as error:
        return [], f"تعذر فحص ماسحات WIA: {error}"


def linux_printers():
    lpstat = shutil.which("lpstat")
    if not lpstat:
        return [], "لم يتم العثور على lpstat. ثبّت CUPS وأدواته."

    result = run_command([lpstat, "-p"])
    if isinstance(result, Exception):
        return [], f"تعذر تشغيل فحص الطابعة: {result}"
    if result.returncode != 0:
        return [], result.stderr.strip() or "تعذر الاتصال بخدمة الطباعة CUPS."

    connection_result = run_command([lpstat, "-v"])
    connections = {}
    if not isinstance(connection_result, Exception) and connection_result.returncode == 0:
        for line in connection_result.stdout.splitlines():
            match = re.match(r"device for (.+?): (.+)", line.strip())
            if match:
                connections[match.group(1)] = match.group(2)

    printers = []
    for line in result.stdout.splitlines():
        line = line.strip()
        match = re.match(r"printer (.+?) is (.+?)(?:\.|$)", line)
        if match:
            name, state = match.groups()
            printers.append((name, state, printer_connection(connections.get(name))))
            continue
        disabled = re.match(r"printer (.+?) disabled(?:\s|$)", line)
        if disabled:
            name = disabled.group(1)
            printers.append((name, "disabled", printer_connection(connections.get(name))))
    return printers, None


def printer_connection(uri):
    if not uri:
        return "الاتصال غير معروف"

    scheme = uri.split(":", 1)[0].lower()
    connection_types = {
        "usb": "USB عبر CUPS",
        "hp": "USB/شبكة عبر HPLIP",
        "ipp": "IPP",
        "ipps": "IPP مشفر",
        "socket": "JetDirect/Socket",
        "lpd": "LPD",
        "dnssd": "اكتشاف شبكة DNS-SD",
        "serial": "Serial",
    }
    return connection_types.get(scheme, f"CUPS backend: {scheme}")


def windows_printers():
    try:
        import win32print

        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        printers = []
        for printer in win32print.EnumPrinters(flags, None, 2):
            status = printer["Status"]
            messages = []
            for flag, label in (
                (win32print.PRINTER_STATUS_OFFLINE, "غير متصلة"),
                (win32print.PRINTER_STATUS_ERROR, "خطأ"),
                (win32print.PRINTER_STATUS_PAPER_OUT, "نفد الورق"),
                (win32print.PRINTER_STATUS_DOOR_OPEN, "الغطاء مفتوح"),
            ):
                if status & flag:
                    messages.append(label)
            state = "، ".join(messages) if messages else "جاهزة حسب النظام"
            driver_environment = "غير معروف"
            printer_handle = None
            try:
                printer_handle = win32print.OpenPrinter(printer["pPrinterName"])
                driver_info = win32print.GetPrinterDriver(printer_handle, None, 2)
                driver_environment = str(driver_info.get("pEnvironment", "غير معروف"))
            except Exception:
                pass
            finally:
                if printer_handle:
                    win32print.ClosePrinter(printer_handle)

            environment = driver_environment.lower()
            if "x64" in environment or "amd64" in environment or "arm64" in environment:
                driver_bitness = "64-bit"
            elif "x86" in environment:
                driver_bitness = "32-bit"
            else:
                driver_bitness = "غير معروف"
            details = (
                f"Driver: {printer['pDriverName']} ({driver_bitness}) | "
                f"Port: {printer['pPortName']} | {driver_environment}"
            )
            printers.append((printer["pPrinterName"], state, details))
        return printers, None
    except ImportError:
        return [], "مكتبة pywin32 غير مثبتة. ثبّت متطلبات المشروع."
    except Exception as error:
        return [], f"تعذر فحص الطابعات: {error}"


def print_devices(title, devices, error, unavailable_message):
    print(f"\n{title}")
    if error:
        print(f"  تعذر الفحص: {error}")
        return False
    if not devices:
        print(f"  {unavailable_message}")
        return False

    all_ready = True
    for device in devices:
        name, state = device[:2]
        details = device[2] if len(device) > 2 else None
        print(f"  - {name}: {state}")
        if details:
            print(f"    {details}")
        if any(
            word in state.lower()
            for word in ("offline", "غير متصلة", "error", "خطأ", "disabled", "معطل")
        ):
            all_ready = False
    return all_ready


def read_devices():
    if os.name == "nt":
        scanners, scanner_error = windows_scanners()
        printers, printer_error = windows_printers()
    elif sys.platform.startswith("linux"):
        scanners, scanner_error = linux_scanners()
        printers, printer_error = linux_printers()
    else:
        return None
    return scanners, scanner_error, printers, printer_error


def show_report(report):
    scanners, scanner_error, printers, printer_error = report
    print("فحص الأجهزة المحلي (لا يحتاج إلى إنترنت)")
    print(f"نظام التشغيل: {platform.system()} ({system_bitness()}, {platform.machine()})")
    print(f"Python: {'64-bit' if sys.maxsize > 2**32 else '32-bit'}")
    scanner_ok = print_devices(
        "الماسحات الضوئية:",
        scanners,
        scanner_error,
        "لم يتم العثور على ماسح متصل.",
    )
    printer_ok = print_devices(
        "الطابعات:",
        printers,
        printer_error,
        "لم يتم العثور على طابعة مُعرّفة.",
    )
    print("\nملاحظة: SANE وWIA/TWAIN واجهات للماسحات؛ الطابعات تستخدم تعريف النظام وCUPS/IPP/USB.")
    print("هذه نتيجة اكتشاف الأجهزة وحالتها، وليست اختبار طباعة أو مسح فعليًا.")
    return 0 if scanner_ok and printer_ok else 1


def main():
    parser = argparse.ArgumentParser(description="فحص الطابعات والماسحات محليًا")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="مراقبة توصيل الأجهزة وإظهار التغييرات كل 3 ثوانٍ",
    )
    args = parser.parse_args()

    report = read_devices()
    if report is None:
        print("هذا الفحص يدعم Linux وWindows فقط.")
        return 2
    if not args.watch:
        return show_report(report)

    print("مراقبة الأجهزة المحلية. اضغط Ctrl+C للإيقاف.")
    previous_report = None
    try:
        while True:
            report = read_devices()
            if report != previous_report:
                if previous_report is not None:
                    print("\nتم رصد تغيير في الأجهزة:")
                show_report(report)
                previous_report = report
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nتم إيقاف مراقبة الأجهزة.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())