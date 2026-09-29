# Scan2scanner

واجهة ويب محلية لمسح المستندات باستخدام ماسح متصل عبر USB.

## المتطلبات

- Linux مع دعم SANE للماسح. على Ubuntu/Debian: `sudo apt install sane-utils`
- Windows 10 أو Windows 7 مع تعريف ماسح WIA متوافق
- Python 3.8 أو أحدث. Windows 7 يتطلب Python 3.8, وهو إصدار منتهي الدعم.
- توصيل الماسح مباشرة بهذا الكمبيوتر، وإتاحة الوصول إليه لمستخدم النظام

تحقق من اكتشاف الجهاز قبل التشغيل:

```bash
scanimage -L
```

إذا لم يظهر الماسح، ثبّت تعريفه/حزمة SANE المناسبة وتحقق من صلاحيات USB. دعم USB يعتمد على طراز الماسح وتعريف SANE المتوفر له.

على Windows يستخدم التطبيق واجهة WIA المدمجة، ويتطلب أن يثبّت تعريف Sharp AR-6020 جهاز مسح WIA في Windows. إذا كان تعريف Sharp المتوفر TWAIN فقط ولا يعرض WIA، فلن يكتشفه هذا التطبيق حتى تتم إضافة تكامل TWAIN منفصل.

## التشغيل

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

على Windows 10 أنشئ البيئة باستخدام `py -3 -m venv .venv`. على Windows 7 استخدم `py -3.8 -m venv .venv`. بعد ذلك فعّل البيئة عبر `.venv\\Scripts\\activate` وثبّت المتطلبات بـ `python -m pip install -r requirements.txt` ثم شغّل `python app.py`.

## أمثلة Rust وGo وErlang

توجد تطبيقات سطر أوامر بديلة في `examples/rust`, `examples/go`, و`examples/erlang`. كل مثال يستخدم `scanimage` من SANE، ويحتاج Linux وتعريف ماسح مدعوماً؛ هذه الأمثلة ليست واجهات ويب ولا تضيف دعماً لـ Windows. تحفظ الصفحة الممسوحة في `scans/scanned.png`.

```bash
rustc examples/rust/scanner.rs -o scanner-rust && ./scanner-rust
go run examples/go/scanner.go
erlc -o /tmp examples/erlang/scanner.erl && erl -noshell -pa /tmp -s scanner main
```

افتح <http://127.0.0.1:8000>. يبقى الماسح موصولاً بالكمبيوتر الذي يشغّل `app.py`؛ فتح الصفحة من جهاز آخر لا ينقل اتصال USB إلى ذلك الجهاز.

## فحص الطابعات والماسحات دون إنترنت

شغّل أداة التشخيص من مجلد المشروع:

```bash
python check_devices.py
```

لمراقبة التوصيل وعرض التغييرات تلقائيًا كل 3 ثوانٍ، شغّل `python check_devices.py --watch` وأوقفه بـ `Ctrl+C`. يعرض التقرير معمارية النظام وPython (32/64-bit)، ونوع اتصال الطابعة وتعريفها، وواجهة الماسح المكتشفة مثل SANE أو WIA.

تفحص الأداة الأجهزة المحلية وحالتها المعلنة من النظام فقط، ولا تطبع أو تمسح مستندًا. على Linux تحتاج إلى `sane-utils` وCUPS (`lpstat`)، وعلى Windows تحتاج إلى متطلبات المشروع وتعريفات WIA للطابعة/الماسح. لا يفحص هذا الإصدار TWAIN؛ فهو مسار ماسح منفصل عن WIA.

## إنشاء ملفات التثبيت

من GitHub Actions شغّل **Build distributables** يدويًا، أو أنشئ tag يبدأ بـ `v` مثل `v1.0.0`. تُرفع النتائج كـ workflow artifacts:

- Windows EXE لـ 32-bit و64-bit، مبنيّان باستخدام Python 3.8 لدعم Windows 7.
- Linux executable وملفا DEB وRPM لمعمارية x86_64.

يجب بناء EXE على Windows وملفات Linux على Linux. ملفات التشغيل المجمّعة لا تحتوي تعريفات الأجهزة؛ يحتاج المسح على Linux إلى SANE (`sane-utils`) والطباعة إلى CUPS، بينما يعتمد Windows على تعريف WIA متوافق. تحفظ النسخة المجمّعة ملفات المسح في مجلد المستخدم.
