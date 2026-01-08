import pyinsane2
from PIL import Image
تهيئة الماسح الضوئي
pyinsane2.init()
try:
    devices = pyinsane2.get_devices()
    if not devices:
        print("❌ لا يوجد ماسح ضوئي متصل.")
        exit()
    scanner = devices[0]
    print(f"📠 جاري استخدام: {scanner.name}")
    # بدء عملية المسح
    scan_session = scanner.scan(multiple=False)
    while True:
        try:
 scan_session.scan.read()
        except EOFError:
            break
    # حفظ الصورة
    image = scan_session.images[-1]    image.save("scanned.png")
    print("✅ تم حفظ الصورة باسم scanned.png")
finally:
    pyinsane2.exit()
