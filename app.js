const scanForm = document.querySelector("#scan-form");
const scanButton = document.querySelector("#scan-button");
const statusMessage = document.querySelector("#status-message");
const imageInput = document.querySelector("#image-input");
const previewImage = document.querySelector("#preview-image");
const previewPdf = document.querySelector("#preview-pdf");
const emptyPreview = document.querySelector("#empty-preview");
const pageCount = document.querySelector("#page-count");
const fileName = document.querySelector("#file-name");
const downloadLink = document.querySelector("#download-link");
const printButton = document.querySelector("#print-button");
const connectionStatus = document.querySelector("#connection-status");
const deviceStatus = document.querySelector("#device-status");
const deviceName = document.querySelector("#device-name");
const deviceDescription = document.querySelector("#device-description");
const systemInfoState = document.querySelector("#system-info-state");
const operatingSystem = document.querySelector("#operating-system");
const systemArchitecture = document.querySelector("#system-architecture");
const pythonArchitecture = document.querySelector("#python-architecture");
const scannerInterface = document.querySelector("#scanner-interface");
const printerList = document.querySelector("#printer-list");

let previewUrl;
let previewType;
let scanInProgress = false;

async function refreshScannerStatus() {
  try {
    const response = await fetch("/api/scanners");
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "تعذر فحص الماسح.");

    const scanner = result.scanners[0];
    if (!scanner) {
      connectionStatus.dataset.state = "offline";
      deviceStatus.dataset.state = "offline";
      scanButton.disabled = true;
      connectionStatus.lastChild.textContent = "لا يوجد ماسح متصل";
      deviceStatus.textContent = "غير متصل";
      deviceName.textContent = "لم يتم العثور على ماسح";
      deviceDescription.textContent = `تحقق من USB وتعريف ${scannerInterface.textContent}`;
      return;
    }

    connectionStatus.dataset.state = "online";
    deviceStatus.dataset.state = "online";
    scanButton.disabled = scanInProgress;
    connectionStatus.lastChild.textContent = "الماسح متصل";
    deviceStatus.textContent = "متصل";
    deviceName.textContent = scanner.name;
    deviceDescription.textContent = scanner.id;
  } catch (error) {
    connectionStatus.dataset.state = "error";
    deviceStatus.dataset.state = "error";
    scanButton.disabled = true;
    connectionStatus.lastChild.textContent = "الخدمة غير متاحة";
    deviceStatus.textContent = "غير متاح";
    deviceName.textContent = "تعذر الاتصال بخدمة المسح";
    deviceDescription.textContent = error.message;
  }
}

async function refreshSystemInfo() {
  try {
    const response = await fetch("/api/system-info");
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "تعذر فحص معلومات النظام.");

    operatingSystem.textContent = result.os_name;
    systemArchitecture.textContent = `${result.os_bitness} (${result.architecture})`;
    pythonArchitecture.textContent = result.python_bitness;
    scannerInterface.textContent = result.scanner_interface;
    systemInfoState.textContent = "تم التحديث";
    systemInfoState.dataset.state = result.printer_error || !result.printers.length ? "warning" : "online";
    printerList.replaceChildren();

    if (result.printer_error) {
      const message = document.createElement("li");
      message.textContent = result.printer_error;
      printerList.append(message);
      return;
    }

    if (!result.printers.length) {
      const message = document.createElement("li");
      message.textContent = "لم يتم العثور على طابعة مُعرّفة.";
      printerList.append(message);
      return;
    }

    for (const printer of result.printers) {
      const item = document.createElement("li");
      const name = document.createElement("strong");
      const details = document.createElement("span");
      name.textContent = `${printer.name}: ${printer.state}`;
      details.textContent = printer.details;
      item.append(name, details);
      printerList.append(item);
    }
  } catch (error) {
    systemInfoState.textContent = "غير متاح";
    systemInfoState.dataset.state = "error";
    printerList.replaceChildren();
    const message = document.createElement("li");
    message.textContent = error.message || "تعذر الاتصال بالخادم المحلي.";
    printerList.append(message);
  }
}

function showDocument(url, name, type) {
  if (previewUrl?.startsWith("blob:") && previewUrl !== url) URL.revokeObjectURL(previewUrl);
  previewUrl = url;
  previewType = type;
  emptyPreview.hidden = true;
  const isPdf = type === "application/pdf";
  previewImage.hidden = isPdf;
  previewPdf.hidden = !isPdf;
  if (isPdf) {
    previewPdf.src = url;
    pageCount.textContent = "PDF";
  } else {
    previewImage.src = url;
    previewPdf.src = "about:blank";
    pageCount.textContent = "صفحة واحدة";
  }
  fileName.textContent = name;
  downloadLink.href = url;
  downloadLink.download = name;
  downloadLink.hidden = false;
  printButton.disabled = false;
}

imageInput.addEventListener("change", () => {
  const file = imageInput.files?.[0];
  if (!file) return;

  const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
  const supportedImage = ["image/png", "image/jpeg", "image/webp"].includes(file.type);
  if (!isPdf && !supportedImage) {
    statusMessage.dataset.state = "error";
    statusMessage.textContent = "اختر ملف PDF أو PNG أو JPG أو WebP.";
    imageInput.value = "";
    return;
  }

  statusMessage.textContent = "";
  statusMessage.dataset.state = "";
  previewUrl = URL.createObjectURL(file);
  showDocument(previewUrl, file.name, isPdf ? "application/pdf" : file.type);
});

printButton.addEventListener("click", () => {
  if (!previewUrl) return;

  if (previewType === "application/pdf") {
    try {
      previewPdf.contentWindow.focus();
      previewPdf.contentWindow.print();
      statusMessage.dataset.state = "success";
      statusMessage.textContent = "اختر الطابعة ثم أكد الطباعة من نافذة النظام.";
      return;
    } catch {
      const printWindow = window.open(previewUrl, "_blank");
      statusMessage.dataset.state = printWindow ? "success" : "error";
      statusMessage.textContent = printWindow
        ? "تعذر فتح نافذة الطباعة مباشرة؛ استخدم أمر الطباعة في عارض PDF."
        : "اسمح بالنوافذ المنبثقة لفتح ملف PDF للطباعة.";
      return;
    }
  }

  const printWindow = window.open("", "_blank");
  if (!printWindow) {
    statusMessage.dataset.state = "error";
    statusMessage.textContent = "اسمح بالنوافذ المنبثقة لفتح معاينة الطباعة.";
    return;
  }

  printWindow.document.title = fileName.textContent;
  const printStyle = printWindow.document.createElement("style");
  printStyle.textContent = "@page { margin: 0; } html, body { width: 100%; height: 100%; margin: 0; } body { display: grid; place-items: center; } img { max-width: 100%; max-height: 100vh; object-fit: contain; } @media print { img { width: 100%; height: 100%; } }";
  const image = printWindow.document.createElement("img");
  image.alt = fileName.textContent;
  image.onload = () => {
    printWindow.focus();
    printWindow.print();
  };
  image.src = new URL(previewUrl, window.location.href).href;
  printWindow.document.head.append(printStyle);
  printWindow.document.body.append(image);
});

scanForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (scanButton.disabled || scanInProgress) return;
  scanInProgress = true;
  scanButton.disabled = true;
  scanButton.dataset.state = "pending";
  statusMessage.dataset.state = "pending";
  statusMessage.textContent = "جارٍ الاتصال بالماسح الضوئي...";

  try {
    const response = await fetch(scanForm.action, { method: "POST" });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || `تعذر بدء المسح (HTTP ${response.status}).`);
    showDocument(result.image_url, result.filename, "image/png");
    statusMessage.dataset.state = "success";
    statusMessage.textContent = result.resolution_dpi
      ? `اكتمل المسح بصيغة PNG بدقة ${result.resolution_dpi} DPI.`
      : "اكتمل المسح بصيغة PNG باستخدام دقة الماسح الافتراضية.";
  } catch (error) {
    statusMessage.dataset.state = "error";
    statusMessage.textContent = error.message || "تعذر الاتصال بخدمة المسح.";
  } finally {
    scanInProgress = false;
    delete scanButton.dataset.state;
    await refreshScannerStatus();
  }
});

refreshScannerStatus();
refreshSystemInfo();
window.setInterval(() => {
  if (document.hidden) return;
  refreshScannerStatus();
  refreshSystemInfo();
}, 5000);
window.addEventListener("focus", () => {
  refreshScannerStatus();
  refreshSystemInfo();
});

window.addEventListener("beforeunload", () => {
  if (previewUrl?.startsWith("blob:")) URL.revokeObjectURL(previewUrl);
});