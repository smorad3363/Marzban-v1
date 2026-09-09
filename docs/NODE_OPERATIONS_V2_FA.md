# Node Operations V2 — راهنمای عملیات و عیب‌یابی

## نمای یکپارچه

Node Operations V2 وضعیت عملیاتی، ترافیک لحظه‌ای، میانگین‌های پایدار ۱ و ۲۴ ساعت، تاریخچه ترافیک و رخدادهای تشخیصی sanitize‌شده را در همان workspace مدیریت Node نمایش می‌دهد. مسیر قدیمی API مربوط به `/api/nodes/usage` برای سازگاری باقی مانده است، اما UI جداگانه Nodes Usage دیگر در ناوبری نمایش داده نمی‌شود.

APIهای افزایشی این قابلیت:

- `GET /api/nodes/operations` برای summary همه Nodeها؛
- `GET /api/node/{node_id}/operations/history` برای تاریخچه persisted و bounded؛
- `GET /api/node/{node_id}/events` برای timeline صفحه‌بندی‌شده و sanitize‌شده.

جمع‌آوری ترافیک Xray مسیر جدیدی ایجاد نمی‌کند: همان collector موجود که reset-counter را برای accounting می‌خواند، نمونه موفق را برای telemetry پایدار نیز ثبت می‌کند.

## عیب‌یابی Node نصب‌شده

روی سرور Node اجرا کنید:

```bash
sudo marzban node doctor
```

یا در hostهایی که CLI اختصاصی Node را استفاده می‌کنند:

```bash
sudo marzban-node node doctor
```

`doctor` فقط بررسی محلی انجام می‌دهد و configuration را تغییر نمی‌دهد. موارد اصلی بررسی‌شده:

- وجود و permission فایل‌های compose و `.env`؛
- اعتبار و تاریخ انقضای certificate پنل که روی Node ذخیره شده؛
- اعتبار certificate و private key خود Node و محدود بودن permission کلید؛
- صحت portها و `EVENT_MAX_ROWS`؛
- render شدن Docker Compose؛
- running/health وضعیت container؛
- تطابق image در حال اجرا با image تنظیم‌شده؛
- تطابق OCI source revision image با revision ثبت‌شده هنگام نصب/آپدیت.

خروجی از `[PASS]`، `[WARN]` و `[FAIL]` استفاده می‌کند. warning به‌تنهایی exit code را fail نمی‌کند؛ وجود failure باعث exit code غیرصفر می‌شود. محتوای PEM، private key یا `.env` در خروجی چاپ نمی‌شود.

## نکات mTLS

مالکیت credentialها تغییر نکرده است: Node فقط certificate پنل موردنیاز قرارداد موجود را دریافت می‌کند و private key پنل روی Node کپی نمی‌شود. certificate/key سرور Node در `/var/lib/marzban-node/` متعلق به runtime Node هستند.

اگر doctor خطای certificate بدهد، فایل‌ها را دستی از پنل دیگری جایگزین نکنید. ابتدا علت provisioning/expiry را بررسی کنید و سپس از مسیر نصب/آپدیت مستند Node استفاده کنید.

## رخدادها و retention

رخدادهای runtime و reconnect قبل از نمایش sanitize می‌شوند. spool محلی و storage سمت پنل bounded هستند؛ telemetry یا persistence failure نباید مسیر accounting یا reconnect موجود را متوقف کند.
