لإضافة *زر Scan* لتشغيل الكود من واجهة ويب بسيطة باستخدام HTML و Python، يمكنك دمج الكود مع *Flask*.

✅ الخطوات:

1. تثبيت Flask (إذا لم يكن مثبتًا):

```bash
pip install flask
```

---

2. `app.py` — كود Python كامل مع زر المسح:

```python
from flask import Flask, render_template, redirect, url_for
import pyinsane2
from PIL import Image
import os

app = Flask(_name_)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan')
def scan():
    pyinsane2.init()
    try:
        devices = pyinsane2.get_devices()
        if not devices:
            return "❌ لا يوجد ماسح ضوئي متصل."
        scanner = devices[0]
        scan_session = scanner.scan(multiple=False)
        while True:
            try:
                scan_session.scan.read()
            except EOFError:
                break
        image = scan_session.images[-1]
        image.save("static/scanned.png")
    finally:
        pyinsane2.exit()
    return redirect(url_for('show_image'))

@app.route('/show')
def show_image():
    return render_template('show.html')

if _name_ == '_main_':
    app.run(debug=True)
```

---

3. `templates/index.html` — زر المسح:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Scan Document</title>
</head>
<body>
    <h1>📄 اضغط لبدء المسح</h1>
<form action="/scan">
        <button type="submit">🔍 Scan</button>
    </form>
</body>
</html>
```

---

4. `templates/show.html` — عرض الصورة:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Scanned Image</title>
</head>
<body>
    <h1>✅ النتيجة:</h1>
    <img src="/static/scanned.png" alt="Scanned Image">
    <br><a href="/">الرجوع</a>
</body>
</html>
```

---

5. شغّل التطبيق:

```bash
python app.py
```

ثم افتح المتصفح على:

```
http://localhost:5000/
```

سترى زر "Scan"، وبالضغط عليه يتم تشغيل الكود والمسح الضوئي.
