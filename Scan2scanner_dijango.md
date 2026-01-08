لإضافة *زر Scan* في مشروع *Django* يقوم بتشغيل الكود لمسح ضوئي باستخدام `pyinsane2`، اتبع الخطوات التالية:

---

✅ 1. إعداد المشروع:

```bash
django-admin startproject scanner_project
cd scanner_project
python manage.py startapp scanapp
```

---

✅ 2. تعديل *views.py* في `scanapp`:

```python
from django.shortcuts import render, redirect
import pyinsane2
from PIL import Image

def index(request):
    return render(request, 'scanapp/index.html')

def scan(request):
    pyinsane2.init()
    try:
        devices = pyinsane2.get_devices()
        if not devices:
            return render(request, 'scanapp/error.html', {"message": "❌ لا يوجد ماسح ضوئي متصل."})
        scanner = devices[0]
        scan_session = scanner.scan(multiple=False)
        while True:
            try:
                scan_session.scan.read()
            except EOFError:
                break
        image = scan_session.images[-1]
        image.save("scanapp/static/scanned.png")
    finally:
        pyinsane2.exit()
    return redirect('show')

def show(request):
    return render(request, 'scanapp/show.html')
```

---

✅ 3. urls.py في `scanner_project/urls.py`:

```python
from django.contrib import admin
from django.urls import path
from scanapp import views

urlpatterns = [
path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('scan/', views.scan, name='scan'),
    path('show/', views.show, name='show'),
]
```

---

✅ 4. القوالب:

- `scanapp/templates/scanapp/index.html`:

```html
<h2>📄 اضغط لبدء المسح</h2>
<form action="/scan/">
    <button type="submit">🔍 Scan</button>
</form>
```

- `scanapp/templates/scanapp/show.html`:

```html
<h2>✅ النتيجة:</h2>
<img src="/static/scanned.png" alt="Scanned Image" />
<br><a href="/">رجوع</a>
```

- `scanapp/templates/scanapp/error.html`:

```html
<h2>{{ message }}</h2>
<a href="/">رجوع</a>
```

---

✅ 5. تشغيل المشروع:

```bash
python manage.py runserver
```

ثم افتح المتصفح على:

```
http://127.0.0.1:8000/
```

واضغط زر *Scan* لبدء عملية المسح وحفظ الصورة.
