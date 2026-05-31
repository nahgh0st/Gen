# discord-3char-hunter

يصطاد يوزرنيم **3 أحرف** على Discord بشكل تلقائي عبر GitHub Actions.

---

## كيف يشتغل

- **أول رن:** يولّد كل الكومبينيشنز الممكنة (46,656 اسم من a-z + 0-9) ويحفظهم في `queue.txt` بترتيب عشوائي
- **كل ساعة:** يجرب اسمين من أول القائمة عبر `PATCH /api/v10/users/@me`
  - ✅ `200` → اليوزرنيم صار لك، يفتح GitHub Issue ويوقف الـ workflow تلقائياً
  - ✗ `400` (محجوز) → يحذفه من القائمة ويمشي
  - ⏳ `429` (rate limit) → يوقف الرن الحالي ويحاول الساعة الجاية
- **القائمة** (`queue.txt`) تتقلص كل رن — تقدر تشوف التقدم

---

## الإعداد

### 1. ارفع الملفات على GitHub repo جديد

```
your-repo/
  .github/workflows/username_hunter.yml
  hunt.py
  README.md
```

### 2. أضف الـ Token كـ Secret

**Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|-------|
| `DISCORD_TOKEN` | توكن حسابك على Discord |

**كيف تجيب التوكن:**
1. افتح Discord في المتصفح (discord.com/app)
2. DevTools → Network
3. اضغط على أي شي → دور على أي request لـ `discord.com/api`
4. Authorization header → القيمة هي توكنك

> ⚠️ لا تحط التوكن في الكود أبداً — GitHub Secret فقط

### 3. فعّل Actions وشغّل يدوياً أول مرة

Actions → **Discord 3-Char Username Hunter** → **Run workflow**

---

## الأرقام

| | |
|--|--|
| إجمالي الأسماء | 46,656 |
| محاولات باليوم | 48 (2 × 24 ساعة) |
| لو 0.5% متاح | ~4 أيام متوسط |
| أقصى وقت (كلهم محجوزين) | ~972 يوم |

---

## الملفات

| ملف | وظيفة |
|-----|-------|
| `hunt.py` | السكريبت الرئيسي |
| `queue.txt` | قائمة الأسماء المتبقية (تتولّد تلقائياً) |
| `claimed.txt` | اسم الحساب بعد النجاح (يوقف الـ workflow) |
| `.github/workflows/username_hunter.yml` | الـ workflow |
