# دليل ERPNext — LoyalPet Project
## من الصفر إلى الإنتاج

---

## 1. ما هو ERPNext وكيف يعمل؟

ERPNext ليس برنامج عادي — هو **تطبيق مبني فوق إطار عمل اسمه Frappe**.

```
┌─────────────────────────────────────┐
│           Frappe Framework          │  ← الأساس (Python + JavaScript)
│                                     │
│  ┌──────────────┐  ┌─────────────┐  │
│  │   ERPNext    │  │  LoyalPet   │  │
│  │  (تطبيق ERP) │  │ (تطبيقنا)  │  │
│  └──────────────┘  └─────────────┘  │
│                                     │
│         يشتغلان معًا على نفس الـ    │
│              Frappe Site            │
└─────────────────────────────────────┘
```

**المفاهيم الأساسية:**

| المصطلح | المعنى |
|---------|--------|
| **Frappe** | إطار العمل — مثل Laravel بالضبط لكن بالبايثون |
| **ERPNext** | تطبيق ERP مبني على Frappe |
| **Custom App** | تطبيقنا الخاص اللي نضيفه فوق ERPNext |
| **Bench** | أداة CLI تدير كل شيء (مثل artisan في Laravel) |
| **Site** | موقع Frappe واحد = قاعدة بيانات + إعدادات |
| **DocType** | جدول في DB مع form تلقائي (مثل Model في Laravel) |

---

## 2. Bench — قلب النظام

`bench` هو الأمر الذي تستخدمه لكل شيء في Frappe/ERPNext.

```bash
# هيكل مجلد bench
frappe-bench/
├── apps/                  ← كل التطبيقات هنا
│   ├── frappe/            ← الإطار الأساسي
│   ├── erpnext/           ← تطبيق ERPNext
│   └── loyalpet/          ← تطبيقنا المخصص ← سنخلقه
├── sites/                 ← المواقع
│   └── loyalpet.local/    ← الموقع المحلي
│       ├── site_config.json
│       └── private/
├── config/                ← إعدادات nginx, supervisor
└── logs/                  ← السجلات
```

```bash
# أوامر bench الأساسية
bench new-app loyalpet           # إنشاء تطبيق جديد
bench new-site loyalpet.local    # إنشاء موقع جديد
bench install-app loyalpet       # تثبيت التطبيق على الموقع
bench start                      # تشغيل بيئة التطوير
bench update                     # تحديث كل شيء
bench migrate                    # تطبيق التغييرات على DB
bench build                      # بناء الـ assets
```

---

## 3. Local Development أولًا — ثم الإنتاج

### لماذا محلي أولًا؟

```
لوكل (Development)          السيرفر (Production)
─────────────────          ──────────────────────
تطوير + تجربة              المستخدمون الحقيقيون
أخطاء مقبولة               لا أخطاء مقبولة
بيانات وهمية               بيانات حقيقية
يشتغل على جهازك            Ubuntu Server
```

**الترتيب الصحيح:**

```
1. تثبيت محلي على جهازك
        │
        ▼
2. تطوير Custom App محليًا
        │
        ▼
3. اختبار كل شيء
        │
        ▼
4. رفع للسيرفر (Production)
        │
        ▼
5. نفس الأوامر — نفس النتيجة
```

---

## 4. التثبيت المحلي (Development)

### المتطلبات

```
نظام التشغيل: Ubuntu 20.04/22.04 أو macOS
(Windows: يشتغل عبر WSL2 — Ubuntu داخل Windows)
```

```bash
# الخطوة 1: تثبيت المتطلبات
sudo apt install python3-dev python3-pip redis-server mariadb-server nodejs npm

# الخطوة 2: تثبيت frappe-bench
pip3 install frappe-bench

# الخطوة 3: إنشاء بيئة bench جديدة
bench init frappe-bench --frappe-branch version-15
cd frappe-bench

# الخطوة 4: تحميل ERPNext
bench get-app erpnext --branch version-15

# الخطوة 5: إنشاء موقع محلي
bench new-site loyalpet.local --db-name loyalpet

# الخطوة 6: تثبيت ERPNext على الموقع
bench --site loyalpet.local install-app erpnext

# الخطوة 7: تشغيل
bench start
# الموقع يشتغل على: http://loyalpet.local:8000
```

---

## 5. Custom App — ما هو ولماذا نحتاجه؟

### لماذا Custom App وليس تعديل ERPNext مباشرة؟

```
❌ تعديل ERPNext مباشرة:
   - عند تحديث ERPNext تضيع تعديلاتك
   - لا يمكن نقله لسيرفر آخر بسهولة
   - خطر على استقرار النظام

✓ Custom App منفصل:
   - محمي من التحديثات
   - قابل للنقل والـ version control
   - منفصل ونظيف
```

### ماذا سيحتوي تطبيقنا LoyalPet؟

```
loyalpet app
│
├── Custom DocTypes (جديدة بالكامل)
│   │
│   ├── 💰 المحفظة
│   │   ├── Wallet                  ← محفظة لكل عميل
│   │   ├── Wallet Transaction      ← سجل كل عملية
│   │   └── Voucher                 ← كروت أنيس
│   │
│   ├── 🐾 الحيوانات
│   │   └── Pet                     ← حيوان مرتبط بعميل
│   │
│   ├── 🏥 البيطرة
│   │   ├── Vet Service Type        ← أنواع الخدمات (ديناميك)
│   │   └── Vet Appointment         ← حجز موعد
│   │
│   └── 🏨 الفندقة
│       ├── Hotel Room Type         ← أنواع الغرف (ديناميك)
│       ├── Hotel Room              ← الغرف الفعلية
│       ├── Hotel Room Service      ← خدمات الغرف (ديناميك)
│       └── Hotel Booking           ← حجز إقامة
│
├── Custom Fields على DocTypes موجودة
│   ├── Customer: custom_app_user_id
│   ├── Sales Order: custom_from_app, custom_app_reference, custom_payment_method
│   ├── Item: custom_show_in_app
│   └── Employee: custom_employee_type  ← (Doctor / Staff / Driver)
│
├── API Endpoints (لـ Laravel)
│   ├── loyalpet.api.products.*         ← قائمة المنتجات والأسعار
│   ├── loyalpet.api.orders.*           ← إنشاء وجلب الطلبات
│   ├── loyalpet.api.wallet.*           ← المحفظة والشحن والخصم
│   ├── loyalpet.api.vet.*              ← البيطرة والمواعيد
│   ├── loyalpet.api.hotel.*            ← الفندقة والحجوزات
│   └── loyalpet.api.pets.*             ← حيوانات العميل
│
├── Order Workflow (Sales Order)
│   ├── Pending Review → Accepted → Out for Delivery → Delivered → Completed
│   └── Pending Review → Rejected → Cancelled
│
├── Webhooks Setup
│   └── إعداد تلقائي للـ webhooks عند تثبيت التطبيق
│
└── Hooks (Event Listeners)
    ├── Customer: after_insert → أشعر Laravel
    ├── Sales Order: on_workflow_action → أشعر Laravel بكل تغيير حالة
    ├── Wallet Transaction: after_insert → أشعر Laravel
    ├── Vet Appointment: on_update → أشعر Laravel
    └── Hotel Booking: on_update → أشعر Laravel
```

---

## 6. إنشاء Custom App

```bash
# داخل مجلد frappe-bench
bench new-app loyalpet
```

سيسألك bench عن معلومات التطبيق:
```
App Title: LoyalPet
App Description: LoyalPet Mobile App Integration
App Publisher: Your Name
App Email: your@email.com
App License: MIT
```

### هيكل التطبيق الناتج

```
apps/loyalpet/
├── loyalpet/                    ← الحزمة الرئيسية
│   ├── __init__.py
│   ├── hooks.py                 ← ← ← أهم ملف
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py         ← API endpoints لـ Laravel
│   │
│   ├── loyalpet/               ← DocTypes المخصصة
│   │   └── doctype/
│   │
│   ├── custom/                 ← Custom fields وتعديلات
│   │   └── custom_fields.py
│   │
│   └── fixtures/               ← بيانات افتراضية تُحمَّل عند التثبيت
│       ├── custom_fields.json
│       └── webhooks.json
│
├── setup.py
└── requirements.txt
```

---

## 7. hooks.py — قلب التطبيق

هذا الملف يخبر Frappe بكل شيء عن تطبيقنا.

```python
# apps/loyalpet/loyalpet/hooks.py

app_name = "loyalpet"
app_title = "LoyalPet"
app_publisher = "LoyalPet Team"
app_description = "Mobile App Integration"
app_version = "1.0.0"

# ──────────────────────────────────────────
# Event Hooks — ما يحصل عند أحداث معينة
# ──────────────────────────────────────────
doc_events = {
    "Customer": {
        "after_insert": "loyalpet.events.customer.on_customer_created",
    },
    "Sales Order": {
        "on_workflow_action": "loyalpet.events.sales_order.on_workflow_action",
    },
    "Item": {
        "after_insert": "loyalpet.events.item.on_item_created",
        "on_update":    "loyalpet.events.item.on_item_updated",
    },
    "Wallet Transaction": {
        "after_insert": "loyalpet.events.wallet.on_transaction_created",
    },
    "Vet Appointment": {
        "on_update": "loyalpet.events.vet.on_appointment_updated",
    },
    "Hotel Booking": {
        "on_update": "loyalpet.events.hotel.on_booking_updated",
    },
}

# ──────────────────────────────────────────
# Scheduled Tasks — مهام مجدولة
# ──────────────────────────────────────────
scheduler_events = {
    "daily": [
        "loyalpet.tasks.send_appointment_reminders",
        "loyalpet.tasks.expire_vouchers",
    ],
    "hourly": [
        "loyalpet.tasks.check_low_stock",
        "loyalpet.tasks.check_hotel_checkouts",
    ],
}

# ──────────────────────────────────────────
# Fixtures — بيانات تُحمَّل عند تثبيت التطبيق
# ──────────────────────────────────────────
fixtures = [
    "Custom Field",    # حقول مخصصة
    "Webhook",         # webhooks جاهزة
    "Role",            # أدوار مخصصة
    "Workflow",        # Sales Order workflow
    "Workflow State",
    "Workflow Action",
]
```

---

## 8. API Endpoints لـ Laravel

الدالات المعرّفة بـ `@frappe.whitelist()` تصبح API endpoints تلقائيًا.

```python
# apps/loyalpet/loyalpet/api/endpoints.py

import frappe
from frappe import _

@frappe.whitelist()
def get_product_list(price_list="Standard Selling", limit=50):
    """
    تُستدعى من Laravel:
    POST /api/method/loyalpet.api.endpoints.get_product_list
    """
    items = frappe.get_list("Item",
        filters={"disabled": 0},
        fields=[
            "name", "item_code", "item_name",
            "description", "item_group"
        ],
        limit=limit
    )

    # جلب الأسعار
    for item in items:
        price = frappe.get_value("Item Price", {
            "item_code": item["item_code"],
            "price_list": price_list,
        }, "price_list_rate")
        item["price"] = price or 0

    return items


@frappe.whitelist()
def create_sales_order(customer_id, items, delivery_date=None):
    """
    إنشاء Sales Order من Laravel
    POST /api/method/loyalpet.api.endpoints.create_sales_order
    """
    # التحقق من العميل
    if not frappe.db.exists("Customer", customer_id):
        frappe.throw(_("العميل غير موجود"), frappe.DoesNotExistError)

    doc = frappe.new_doc("Sales Order")
    doc.customer        = customer_id
    doc.delivery_date   = delivery_date or frappe.utils.add_days(frappe.utils.today(), 3)
    doc.order_type      = "Sales"
    doc.custom_from_app = 1    # حقل مخصص يدل أن الطلب من الموبايل

    for item in items:
        doc.append("items", {
            "item_code": item["item_code"],
            "qty":       item["qty"],
            "rate":      item.get("rate"),   # لو None، ERPNext يجيب السعر تلقائي
        })

    doc.insert(ignore_permissions=True)
    doc.submit()

    return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def get_customer_orders(customer_id, limit=20):
    """
    جلب طلبات عميل معين
    """
    return frappe.get_list("Sales Order",
        filters={"customer": customer_id, "docstatus": ["!=", 2]},
        fields=["name", "status", "grand_total", "delivery_date", "transaction_date"],
        order_by="creation desc",
        limit=limit
    )


@frappe.whitelist()
def get_stock_balance(item_code, warehouse=None):
    """
    جلب رصيد المخزون لمنتج معين
    """
    from erpnext.stock.utils import get_stock_balance
    warehouse = warehouse or frappe.db.get_single_value("Stock Settings", "default_warehouse")
    balance   = get_stock_balance(item_code, warehouse)
    return {"item_code": item_code, "warehouse": warehouse, "qty": balance}
```

---

## 9. Events — إرسال Webhooks لـ Laravel

```python
# apps/loyalpet/loyalpet/events/sales_order.py

import frappe
import requests
from frappe import _

LARAVEL_WEBHOOK_URL = frappe.conf.get("laravel_webhook_url", "")
WEBHOOK_SECRET      = frappe.conf.get("laravel_webhook_secret", "")

def on_order_submitted(doc, method):
    """يُشتغل تلقائيًا لما يتقبّل Sales Order"""
    _send_to_laravel("Sales Order:on_submit", {
        "name":        doc.name,
        "customer":    doc.customer,
        "grand_total": doc.grand_total,
        "status":      doc.status,
        "owner":       doc.owner,
        "items":       [
            {"item_code": i.item_code, "qty": i.qty, "rate": i.rate}
            for i in doc.items
        ],
    })

def on_order_cancelled(doc, method):
    """يُشتغل تلقائيًا لما يُلغى Sales Order"""
    _send_to_laravel("Sales Order:on_cancel", {
        "name":        doc.name,
        "customer":    doc.customer,
        "grand_total": doc.grand_total,
    })

def _send_to_laravel(event: str, data: dict):
    """إرسال webhook لـ Laravel في الخلفية"""
    if not LARAVEL_WEBHOOK_URL:
        return

    import hashlib, hmac, json, time

    payload   = json.dumps({"event": event, "data": data, "timestamp": time.time()})
    signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    try:
        requests.post(
            f"{LARAVEL_WEBHOOK_URL}/api/v1/webhooks/erp",
            data=payload,
            headers={
                "Content-Type":       "application/json",
                "X-ERPNext-Signature": signature,
            },
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        frappe.log_error(f"Webhook failed: {str(e)}", "LoyalPet Webhook Error")
```

---

## 10. Custom Fields — حقول مخصصة على DocTypes موجودة

بدل إنشاء DocTypes جديدة، نضيف حقولًا على الموجودة.

```python
# apps/loyalpet/loyalpet/custom/custom_fields.py

custom_fields = {
    "Customer": [
        {
            "fieldname":    "custom_app_user_id",
            "label":        "App User ID",
            "fieldtype":    "Data",
            "insert_after": "customer_name",
            "read_only":    1,
            "description":  "ID المستخدم في Laravel App",
        },
    ],
    "Sales Order": [
        {
            "fieldname":    "custom_from_app",
            "label":        "Ordered from App",
            "fieldtype":    "Check",
            "insert_after": "order_type",
            "default":      0,
        },
        {
            "fieldname":    "custom_app_reference",
            "label":        "App Order Reference",
            "fieldtype":    "Data",
            "insert_after": "custom_from_app",
            "read_only":    1,
        },
        {
            "fieldname":    "custom_payment_method",
            "label":        "Payment Method",
            "fieldtype":    "Select",
            "options":      "wallet\ncash_on_delivery",
            "insert_after": "custom_app_reference",
        },
        {
            "fieldname":    "custom_rejection_reason",
            "label":        "Rejection Reason",
            "fieldtype":    "Small Text",
            "insert_after": "custom_payment_method",
            "read_only":    1,
        },
    ],
    "Item": [
        {
            "fieldname":    "custom_show_in_app",
            "label":        "Show in Mobile App",
            "fieldtype":    "Check",
            "insert_after": "disabled",
            "default":      1,
        },
    ],
    "Employee": [
        {
            "fieldname":    "custom_employee_type",
            "label":        "Employee Type",
            "fieldtype":    "Select",
            "options":      "Staff\nDoctor\nDriver",
            "insert_after": "employee_name",
            "default":      "Staff",
        },
    ],
}
```

```python
# hooks.py — تطبيق الحقول عند التثبيت
def after_install():
    from loyalpet.custom.custom_fields import custom_fields
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(custom_fields)
    frappe.db.commit()
```

---

## 11. Fixtures — إعداد Webhooks تلقائيًا عند التثبيت

```json
// apps/loyalpet/loyalpet/fixtures/webhooks.json
[
  {
    "doctype": "Webhook",
    "webhook_doctype": "Sales Order",
    "webhook_docevent": "on_submit",
    "request_url": "{{ laravel_url }}/api/v1/webhooks/erp",
    "request_method": "POST",
    "webhook_secret": "{{ webhook_secret }}",
    "enabled": 1,
    "webhook_data": [
      {"fieldname": "name",        "key": "name"},
      {"fieldname": "customer",    "key": "customer"},
      {"fieldname": "grand_total", "key": "grand_total"},
      {"fieldname": "status",      "key": "status"}
    ]
  },
  {
    "doctype": "Webhook",
    "webhook_doctype": "Item",
    "webhook_docevent": "on_update",
    "request_url": "{{ laravel_url }}/api/v1/webhooks/erp",
    "request_method": "POST",
    "enabled": 1
  }
]
```

---

## 12. إعدادات site_config.json

هذا الملف يحتوي على الإعدادات السرية للموقع.

```json
// sites/loyalpet.local/site_config.json
{
  "db_name":                 "loyalpet",
  "db_password":             "...",
  "db_host":                 "localhost",

  "laravel_webhook_url":     "http://localhost:8080",
  "laravel_webhook_secret":  "your-secret-key-here",

  "encryption_key":          "..."
}
```

---

## 13. Development Workflow اليومي

```bash
# 1. شغّل بيئة التطوير
cd frappe-bench
bench start

# 2. بعد أي تغيير في Python
bench --site loyalpet.local migrate
# أو فقط
bench restart

# 3. بعد تغيير Custom Fields
bench --site loyalpet.local migrate

# 4. لو غيّرت hooks.py
bench restart

# 5. اختبار API من الـ terminal
bench --site loyalpet.local execute \
  loyalpet.api.endpoints.get_product_list \
  --kwargs '{"limit": 5}'

# 6. رؤية السجلات
tail -f logs/worker.log
tail -f logs/web.log
```

---

## 14. Deployment — الرفع للإنتاج

### متطلبات السيرفر

```
الحد الأدنى:       الموصى به:
──────────────     ──────────────
OS: Ubuntu 22.04   OS: Ubuntu 22.04
RAM: 4 GB          RAM: 8 GB
CPU: 2 cores       CPU: 4 cores
Storage: 40 GB     Storage: 80 GB SSD
```

**خيارات الاستضافة:**

| الخيار | السعر | المناسب لـ |
|--------|-------|-----------|
| **Frappe Cloud** | $25-50/شهر | أسهل — لا تحتاج إدارة سيرفر |
| **DigitalOcean** | $24/شهر | مرونة + تحكم كامل |
| **Hetzner** | €8-15/شهر | الأرخص مع أداء ممتاز |
| **Linode/Akamai** | $24/شهر | موثوق |

### خطوات الـ Deployment

```bash
# ═══════════════════════════════════════
# على السيرفر (Ubuntu 22.04)
# ═══════════════════════════════════════

# 1. تثبيت المتطلبات
sudo apt update && sudo apt upgrade -y
sudo apt install python3-dev python3-pip redis-server \
     mariadb-server nodejs npm git -y

# 2. إنشاء مستخدم للتطبيق (لا تشغّل كـ root)
sudo adduser frappe
sudo usermod -aG sudo frappe
su - frappe

# 3. تثبيت bench
pip3 install frappe-bench

# 4. إنشاء بيئة الإنتاج
bench init --frappe-branch version-15 frappe-bench
cd frappe-bench

# 5. تحميل ERPNext
bench get-app erpnext --branch version-15

# 6. تحميل تطبيقنا من Git
bench get-app loyalpet https://github.com/your-org/loyalpet-erp.git

# 7. إنشاء الموقع
bench new-site loyalpet.example.com \
  --db-name loyalpet_prod \
  --admin-password "strong-password-here"

# 8. تثبيت التطبيقات
bench --site loyalpet.example.com install-app erpnext
bench --site loyalpet.example.com install-app loyalpet

# 9. إعداد الإنتاج (nginx + supervisor)
sudo bench setup production frappe
sudo bench setup nginx
sudo supervisorctl reload
```

### نقل التطوير المحلي للسيرفر

```bash
# الكود يكون في Git دائمًا
# على المحلي:
git add .
git commit -m "feat: add custom fields"
git push origin main

# على السيرفر:
cd frappe-bench/apps/loyalpet
git pull origin main

cd ~/frappe-bench
bench --site loyalpet.example.com migrate
sudo supervisorctl restart all
```

---

## 15. الفرق بين بيئة التطوير والإنتاج

```
بيئة التطوير (محلي)        بيئة الإنتاج (السيرفر)
─────────────────────      ─────────────────────────
bench start                nginx + gunicorn
يشتغل على port 8000        يشتغل على port 80/443
بدون SSL                   SSL مطلوب (Let's Encrypt)
hot reload تلقائي          يحتاج restart بعد تغيير
أخطاء تظهر في terminal     أخطاء في logs فقط
```

```bash
# إعداد SSL تلقائي على السيرفر
sudo bench setup lets-encrypt loyalpet.example.com
```

---

## 16. خلاصة الخطوات للمشروع

```
المرحلة 1 — الإعداد المحلي (أسبوع 1)
─────────────────────────────────────
✓ تثبيت Frappe Bench محليًا
✓ تثبيت ERPNext
✓ إعداد الشركة والعملة (LYD)
✓ إنشاء loyalpet custom app

المرحلة 2 — التطوير (أسابيع 2-4)
────────────────────────────────
✓ إضافة Custom Fields
✓ كتابة API Endpoints
✓ إعداد Event Hooks
✓ اختبار مع Laravel محليًا

المرحلة 3 — الإنتاج (بعد الاختبار)
─────────────────────────────────
✓ تأجير سيرفر Ubuntu
✓ نشر ERPNext + loyalpet app
✓ إعداد SSL
✓ ربط مع Laravel Production
```

---

## 17. أسئلة مهمة قبل البدء

- [x] ما هي العملة الرئيسية؟ → LYD — الدينار الليبي
- [x] ما هي الـ DocTypes؟ → موثقة في Section 18
- [x] هل نحتاج Approval Workflow؟ → نعم، موثق في Section 19
- [x] من سيدير ERPNext؟ → فريق داخلي (موظفون + أدمن)
- [x] هل المستخدمون يدخلون ERPNext؟ → الموظفون نعم، العملاء عبر الموبايل فقط

---

## 18. Custom DocTypes — التعريف الكامل

### 18.1 المحفظة — Wallet

```python
# DocType: Wallet
{
    "doctype": "DocType",
    "name": "Wallet",
    "module": "LoyalPet",
    "fields": [
        {"fieldname": "customer",   "fieldtype": "Link",     "options": "Customer", "reqd": 1},
        {"fieldname": "balance",    "fieldtype": "Currency",  "default": 0, "read_only": 1},
        {"fieldname": "currency",   "fieldtype": "Data",      "default": "LYD"},
        {"fieldname": "is_frozen",  "fieldtype": "Check",     "default": 0},
    ],
    "autoname": "field:customer",
}

# DocType: Wallet Transaction
{
    "doctype": "DocType",
    "name": "Wallet Transaction",
    "module": "LoyalPet",
    "fields": [
        {"fieldname": "wallet",          "fieldtype": "Link",    "options": "Wallet", "reqd": 1},
        {"fieldname": "type",            "fieldtype": "Select",  "options": "credit\ndebit", "reqd": 1},
        {"fieldname": "amount",          "fieldtype": "Currency", "reqd": 1},
        {"fieldname": "balance_before",  "fieldtype": "Currency", "read_only": 1},
        {"fieldname": "balance_after",   "fieldtype": "Currency", "read_only": 1},
        {"fieldname": "source",          "fieldtype": "Select",
         "options": "mypay_topup\nanis_voucher\norder_payment\norder_refund\nadmin_adjustment"},
        {"fieldname": "reference",       "fieldtype": "Data"},
        {"fieldname": "status",          "fieldtype": "Select",
         "options": "Completed\nReversed\nPending", "default": "Completed"},
    ],
}

# DocType: Voucher
{
    "doctype": "DocType",
    "name": "Voucher",
    "module": "LoyalPet",
    "fields": [
        {"fieldname": "code_hash",    "fieldtype": "Data",     "unique": 1, "reqd": 1},
        {"fieldname": "amount",       "fieldtype": "Currency",  "reqd": 1},
        {"fieldname": "batch_id",     "fieldtype": "Data"},
        {"fieldname": "status",       "fieldtype": "Select",
         "options": "Available\nRedeemed\nExpired\nDisabled", "default": "Available"},
        {"fieldname": "redeemed_by",  "fieldtype": "Link",     "options": "Customer"},
        {"fieldname": "redeemed_at",  "fieldtype": "Datetime"},
        {"fieldname": "expires_at",   "fieldtype": "Datetime"},
    ],
}
```

### 18.2 الحيوانات — Pet

```python
# DocType: Pet
{
    "doctype": "DocType",
    "name": "Pet",
    "module": "LoyalPet",
    "fields": [
        {"fieldname": "customer",    "fieldtype": "Link",   "options": "Customer", "reqd": 1},
        {"fieldname": "pet_name",    "fieldtype": "Data",   "reqd": 1},
        {"fieldname": "species",     "fieldtype": "Select",
         "options": "كلب\nقطة\nطير\nأرنب\nأخرى"},
        {"fieldname": "breed",       "fieldtype": "Data"},
        {"fieldname": "birth_date",  "fieldtype": "Date"},
        {"fieldname": "weight",      "fieldtype": "Float"},
        {"fieldname": "medical_notes","fieldtype": "Small Text"},
        {"fieldname": "photo",       "fieldtype": "Attach Image"},
    ],
    "autoname": "naming_series",
    "naming_series": "PET-.####",
}
```

### 18.3 البيطرة — Vet

```python
# DocType: Vet Service Type (ديناميك — يضيفه الأدمن)
{
    "doctype": "DocType",
    "name": "Vet Service Type",
    "module": "LoyalPet",
    "fields": [
        {"fieldname": "service_name", "fieldtype": "Data",     "reqd": 1},
        {"fieldname": "description",  "fieldtype": "Small Text"},
        {"fieldname": "price",        "fieldtype": "Currency",  "reqd": 1},
        {"fieldname": "is_active",    "fieldtype": "Check",     "default": 1},
    ],
}

# DocType: Vet Appointment
{
    "doctype": "DocType",
    "name": "Vet Appointment",
    "module": "LoyalPet",
    "fields": [
        {"fieldname": "customer",         "fieldtype": "Link",     "options": "Customer", "reqd": 1},
        {"fieldname": "service_type",     "fieldtype": "Link",     "options": "Vet Service Type", "reqd": 1},
        {"fieldname": "doctor",           "fieldtype": "Link",     "options": "Employee",
         "description": "مفلتر: custom_employee_type = Doctor"},
        {"fieldname": "appointment_date", "fieldtype": "Date",     "reqd": 1},
        {"fieldname": "appointment_time", "fieldtype": "Time",     "reqd": 1},
        {"fieldname": "status",           "fieldtype": "Select",
         "options": "Pending\nConfirmed\nCompleted\nCancelled", "default": "Pending"},
        {"fieldname": "notes",            "fieldtype": "Small Text"},
        {"fieldname": "total_amount",     "fieldtype": "Currency",  "read_only": 1},
    ],
    "autoname": "naming_series",
    "naming_series": "VET-APT-.####",
}
```

### 18.4 الفندقة — Hotel

```python
# DocType: Hotel Room Type (ديناميك — يضيفه الأدمن)
{
    "doctype": "DocType",
    "name": "Hotel Room Type",
    "module": "LoyalPet",
    "fields": [
        {"fieldname": "type_name",        "fieldtype": "Data",     "reqd": 1},
        {"fieldname": "description",      "fieldtype": "Small Text"},
        {"fieldname": "price_per_night",  "fieldtype": "Currency",  "reqd": 1},
        {"fieldname": "is_active",        "fieldtype": "Check",     "default": 1},
    ],
}

# DocType: Hotel Room Service (ديناميك — أكل، عناية، لعب...)
{
    "doctype": "DocType",
    "name": "Hotel Room Service",
    "module": "LoyalPet",
    "fields": [
        {"fieldname": "service_name",  "fieldtype": "Data",     "reqd": 1},
        {"fieldname": "description",   "fieldtype": "Small Text"},
        {"fieldname": "price_per_day", "fieldtype": "Currency",  "reqd": 1},
        {"fieldname": "is_active",     "fieldtype": "Check",     "default": 1},
    ],
}

# DocType: Hotel Room
{
    "doctype": "DocType",
    "name": "Hotel Room",
    "module": "LoyalPet",
    "fields": [
        {"fieldname": "room_number", "fieldtype": "Data",  "reqd": 1, "unique": 1},
        {"fieldname": "room_type",   "fieldtype": "Link",  "options": "Hotel Room Type", "reqd": 1},
        {"fieldname": "is_active",   "fieldtype": "Check", "default": 1},
    ],
}

# DocType: Hotel Booking
{
    "doctype": "DocType",
    "name": "Hotel Booking",
    "module": "LoyalPet",
    "fields": [
        {"fieldname": "customer",        "fieldtype": "Link",     "options": "Customer", "reqd": 1},
        {"fieldname": "room",            "fieldtype": "Link",     "options": "Hotel Room", "reqd": 1},
        {"fieldname": "check_in_date",   "fieldtype": "Date",     "reqd": 1},
        {"fieldname": "check_out_date",  "fieldtype": "Date",     "reqd": 1},
        {"fieldname": "total_nights",    "fieldtype": "Int",      "read_only": 1},
        {"fieldname": "status",          "fieldtype": "Select",
         "options": "Pending\nConfirmed\nChecked In\nChecked Out\nCancelled", "default": "Pending"},
        {"fieldname": "payment_method",  "fieldtype": "Select",
         "options": "wallet\ncash_on_delivery"},
        {"fieldname": "total_amount",    "fieldtype": "Currency",  "read_only": 1},
        {"fieldname": "services",        "fieldtype": "Table",
         "options": "Hotel Booking Service"},  # Child Table
        {"fieldname": "notes",           "fieldtype": "Small Text"},
    ],
    "autoname": "naming_series",
    "naming_series": "HTL-BKG-.####",
}

# DocType: Hotel Booking Service (Child Table)
{
    "doctype": "DocType",
    "name": "Hotel Booking Service",
    "istable": 1,
    "fields": [
        {"fieldname": "service",  "fieldtype": "Link",     "options": "Hotel Room Service", "reqd": 1},
        {"fieldname": "amount",   "fieldtype": "Currency",  "read_only": 1},
    ],
}
```

---

## 19. Order Workflow — Sales Order

```python
# apps/loyalpet/loyalpet/fixtures/workflow.json
{
    "doctype": "Workflow",
    "name": "Sales Order Workflow",
    "document_type": "Sales Order",
    "is_active": 1,
    "workflow_state_field": "custom_workflow_state",
    "states": [
        {"state": "Pending Review", "doc_status": "1", "allow_edit": "Sales Manager"},
        {"state": "Accepted",       "doc_status": "1", "allow_edit": "Sales Manager"},
        {"state": "Rejected",       "doc_status": "1", "allow_edit": "Sales Manager"},
        {"state": "Out for Delivery","doc_status": "1", "allow_edit": "Sales Manager"},
        {"state": "Delivered",      "doc_status": "1", "allow_edit": "Sales Manager"},
        {"state": "Completed",      "doc_status": "1", "allow_edit": "Sales Manager"},
        {"state": "Cancelled",      "doc_status": "2", "allow_edit": "Sales Manager"},
    ],
    "transitions": [
        {"state": "Pending Review", "action": "Accept",   "next_state": "Accepted",        "allowed": "Sales Manager"},
        {"state": "Pending Review", "action": "Reject",   "next_state": "Rejected",         "allowed": "Sales Manager"},
        {"state": "Rejected",       "action": "Cancel",   "next_state": "Cancelled",        "allowed": "Sales Manager"},
        {"state": "Accepted",       "action": "Dispatch", "next_state": "Out for Delivery", "allowed": "Sales Manager"},
        {"state": "Out for Delivery","action": "Deliver", "next_state": "Delivered",        "allowed": "Sales Manager"},
        {"state": "Delivered",      "action": "Complete", "next_state": "Completed",        "allowed": "Sales Manager"},
    ]
}
```

```
الموظف في ERPNext:
  Pending Review → [Accept]  → Accepted        → خصم المحفظة (لو wallet)
  Pending Review → [Reject]  → Rejected        → لا خصم
  Accepted       → [Dispatch]→ Out for Delivery → إشعار "طلبك في الطريق"
  Out for Delivery→[Deliver] → Delivered        → إشعار "تم التسليم"
  Delivered      → [Complete]→ Completed        → إشعار "اكتمل طلبك"
```

---

## 20. API Endpoints — loyalpet Custom App

```python
# apps/loyalpet/loyalpet/api/

# ────── المنتجات ──────
@frappe.whitelist()
def get_product_list(limit=50): ...          # GET products

# ────── الطلبات ──────
@frappe.whitelist()
def create_sales_order(customer_id, items, payment_method): ...
@frappe.whitelist()
def get_customer_orders(customer_id, limit=20): ...

# ────── المحفظة ──────
@frappe.whitelist()
def get_wallet_balance(customer_id): ...
@frappe.whitelist()
def get_wallet_transactions(customer_id, limit=20): ...
@frappe.whitelist()
def topup_wallet(customer_id, amount, reference, source): ...
    # يُستدعى من Laravel بعد تأكيد MyPay webhook
    # يحدث Wallet.balance + ينشئ Wallet Transaction
@frappe.whitelist()
def redeem_voucher(customer_id, code_hash): ...
    # يتحقق من Voucher → يشحن المحفظة

# ────── البيطرة ──────
@frappe.whitelist()
def get_vet_service_types(): ...             # الخدمات المتاحة (ديناميك)
@frappe.whitelist()
def get_doctors(): ...                       # الأطباء (Employee filtered by type=Doctor)
@frappe.whitelist()
def get_available_slots(doctor, date): ...   # المواعيد المتاحة
@frappe.whitelist()
def create_vet_appointment(customer_id, service_type, doctor, date, time): ...

# ────── الفندقة ──────
@frappe.whitelist()
def get_room_types(): ...                    # أنواع الغرف (ديناميك)
@frappe.whitelist()
def get_room_services(): ...                 # الخدمات المتاحة (ديناميك)
@frappe.whitelist()
def get_available_rooms(room_type, check_in, check_out): ...
@frappe.whitelist()
def create_hotel_booking(customer_id, room, check_in, check_out, services, payment_method): ...

# ────── الحيوانات ──────
@frappe.whitelist()
def get_customer_pets(customer_id): ...
@frappe.whitelist()
def create_pet(customer_id, pet_name, species, breed, birth_date): ...
```

---

## 21. Events — إرسال Webhooks لـ Laravel

```python
# apps/loyalpet/loyalpet/events/sales_order.py

def on_workflow_action(doc, method):
    """يُشتغل عند كل تغيير في حالة Sales Order Workflow"""

    state = doc.custom_workflow_state

    payload = {
        "name":           doc.name,
        "customer":       doc.customer,
        "grand_total":    doc.grand_total,
        "workflow_state": state,
        "payment_method": doc.custom_payment_method,
    }

    if state == "Rejected":
        payload["rejection_reason"] = doc.custom_rejection_reason

    if state == "Accepted" and doc.custom_payment_method == "wallet":
        # خصم المحفظة هنا
        _debit_wallet(doc.customer, doc.grand_total, doc.name)

    _send_to_laravel(f"Sales Order:{state}", payload)


def _debit_wallet(customer_id, amount, order_name):
    """خصم المحفظة بعد قبول الطلب"""
    wallet = frappe.get_doc("Wallet", customer_id)

    if wallet.is_frozen:
        frappe.throw("المحفظة مجمدة")

    if wallet.balance < amount:
        frappe.throw("رصيد غير كافٍ — يرجى شحن المحفظة")

    balance_before = wallet.balance
    wallet.balance -= amount
    wallet.save(ignore_permissions=True)

    frappe.get_doc({
        "doctype":        "Wallet Transaction",
        "wallet":         wallet.name,
        "type":           "debit",
        "amount":         amount,
        "balance_before": balance_before,
        "balance_after":  wallet.balance,
        "source":         "order_payment",
        "reference":      order_name,
        "status":         "Completed",
    }).insert(ignore_permissions=True)
```

```python
# apps/loyalpet/loyalpet/events/wallet.py

def on_transaction_created(doc, method):
    """إشعار Laravel بكل عملية محفظة"""
    _send_to_laravel("Wallet Transaction:created", {
        "wallet":    doc.wallet,
        "type":      doc.type,
        "amount":    doc.amount,
        "balance":   doc.balance_after,
        "source":    doc.source,
        "reference": doc.reference,
    })
```

```python
# apps/loyalpet/loyalpet/events/vet.py

def on_appointment_updated(doc, method):
    """إشعار Laravel بتغيير حالة الموعد"""
    _send_to_laravel("Vet Appointment:updated", {
        "name":     doc.name,
        "customer": doc.customer,
        "status":   doc.status,
        "date":     str(doc.appointment_date),
        "time":     str(doc.appointment_time),
    })
```

```python
# apps/loyalpet/loyalpet/events/hotel.py

def on_booking_updated(doc, method):
    """إشعار Laravel بتغيير حالة الحجز"""
    _send_to_laravel("Hotel Booking:updated", {
        "name":     doc.name,
        "customer": doc.customer,
        "status":   doc.status,
    })
```
