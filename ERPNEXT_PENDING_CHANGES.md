# طلبات تعديل معلّقة على ERPNext — للـ AI اللي عنده وصول لـ Bench

> هذا الملف تجميع لكل التعديلات اللي محتاجينها في ERPNext (تطبيق `loyalpet`) لحد دلوقتي،
> جمعتها في مكان واحد بدل ما تتبعت منفصلة. ابعت المحتوى اللي تحت (من "ابدأ البرومبت" لحد
> "نهاية البرومبت") كامل للـ AI التاني دفعة واحدة.

---

## ابدأ البرومبت

أنت شغال على مشروع ERPNext (Frappe Framework) فيه تطبيق مخصص اسمه loyalpet مبني فوقه.
مطلوب منك 3 مهام مستقلة عن بعض: إضافة مجموعة حقول مخصصة (Custom Fields)، تسجيل 3
Webhooks، وتعديل دالة واحدة موجودة. نفّذهم بالترتيب، ووقف وابلغني لو أي مهمة فيها مشكلة
بدل ما تكمل للي بعدها.

## مهمة 1 — حقول مخصصة (Custom Fields)

ضيف الحقول دي في `custom_fields.py` بتاع تطبيق loyalpet، كل مجموعة جوه قائمة الـ DocType
بتاعتها (لو القائمة مش موجودة زي "Product Bundle"، أنشئها كقائمة جديدة):

**Item** (جنب `custom_show_in_app` الموجود):
| fieldname | label | fieldtype | insert_after | default |
|---|---|---|---|---|
| `custom_is_featured` | مميز في التطبيق | Check | custom_show_in_app | "0" |
| `custom_featured_order` | ترتيب الظهور المميز | Int | custom_is_featured | "0" |

**Product Bundle** (قائمة جديدة):
| fieldname | label | fieldtype | insert_after |
|---|---|---|---|
| `custom_image` | صورة الباقة | Attach Image | description |

**Sales Order** (جنب `custom_rejection_reason` الموجود، آخر حقل في القائمة):
| fieldname | label | fieldtype | insert_after |
|---|---|---|---|
| `custom_recipient_name` | اسم المستلم | Data | custom_rejection_reason |
| `custom_recipient_phone` | هاتف المستلم | Data | custom_recipient_name |
| `custom_delivery_address` | عنوان التوصيل | Small Text | custom_recipient_phone |
| `custom_notes` | ملاحظات | Small Text | custom_delivery_address |

**تطبيق الحقول فعليًا** (التطبيق already مثبت، تعديل الملف بس مش كافي):
```python
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from loyalpet.custom.custom_fields import custom_fields
create_custom_fields(custom_fields)
frappe.db.commit()
```
الدالة دي آمنة تتكرر (idempotent) — لو أي حقل موجود أصلًا مش هتكرره أو تبوظه.

**تحقق:**
```
GET /api/resource/Item?fields=["name","custom_is_featured","custom_featured_order"]&limit_page_length=1
GET /api/resource/Product Bundle?fields=["name","custom_image"]&limit_page_length=1
GET /api/resource/Sales Order?fields=["name","custom_recipient_name","custom_recipient_phone","custom_delivery_address","custom_notes"]&limit_page_length=1
```

---

## مهمة 2 — تسجيل 3 Webhooks

ضيف السجلات دي في `fixtures/webhooks.json` بتاع تطبيق loyalpet (لو الملف مش موجود أنشئه،
ولو موجود ضيف عليه من غير ما تمسح أي webhook موجود فيه):

```json
[
  {
    "doctype": "Webhook",
    "webhook_doctype": "Item",
    "webhook_docevent": "on_update",
    "request_url": "{LARAVEL_URL}/api/v1/webhooks/erp",
    "request_method": "POST",
    "webhook_secret": "8da361e75fa3d411042b13fd5aa2d006a1c44ec726c62d01",
    "enabled": 1
  },
  {
    "doctype": "Webhook",
    "webhook_doctype": "Item Group",
    "webhook_docevent": "on_update",
    "request_url": "{LARAVEL_URL}/api/v1/webhooks/erp",
    "request_method": "POST",
    "webhook_secret": "8da361e75fa3d411042b13fd5aa2d006a1c44ec726c62d01",
    "enabled": 1
  },
  {
    "doctype": "Webhook",
    "webhook_doctype": "Product Bundle",
    "webhook_docevent": "on_update",
    "request_url": "{LARAVEL_URL}/api/v1/webhooks/erp",
    "request_method": "POST",
    "webhook_secret": "8da361e75fa3d411042b13fd5aa2d006a1c44ec726c62d01",
    "enabled": 1
  }
]
```
استبدل `{LARAVEL_URL}` برابط سيرفر Laravel الفعلي المتاح من نفس الشبكة/الجهاز اللي شغال
عليه ERPNext (اسأل المستخدم لو مش متأكد، ما تخمنش).

**تطبيق الـ fixtures فعليًا:**
```
bench --site <site-name> execute --kwargs "{'fixtures': ['Webhook']}" frappe.utils.fixtures.sync_fixtures
```
أو أبسط: من واجهة ERPNext نفسها (Desk → Webhook → New) لو الطريقة البرمجية عملت مشاكل —
المهم يبقى فيه 3 سجلات Webhook فعليين في النهاية بنفس القيم اللي فوق.

**تحقق:**
```
GET /api/resource/Webhook?fields=["name","webhook_doctype","webhook_docevent","enabled"]
```

---

## مهمة 3 — تعديل دالة `create_sales_order`

الدالة دي موجودة على الأغلب في `apps/loyalpet/loyalpet/api/orders.py` (لو مكانها مختلف،
دوّر عليها بالاسم في المشروع كله). استبدلها بالنسخة دي بالظبط:

```python
@frappe.whitelist()
def create_sales_order(customer_id, items, payment_method, recipient_name,
                        recipient_phone, delivery_address, notes=None, delivery_date=None):
    """
    إنشاء Sales Order من Laravel
    POST /api/method/loyalpet.api.orders.create_sales_order
    """
    if not frappe.db.exists("Customer", customer_id):
        frappe.throw(_("العميل غير موجود"), frappe.DoesNotExistError)

    doc = frappe.new_doc("Sales Order")
    doc.customer = customer_id
    doc.delivery_date = delivery_date or frappe.utils.add_days(frappe.utils.today(), 3)
    doc.order_type = "Sales"
    doc.custom_from_app = 1
    doc.custom_payment_method = payment_method
    doc.custom_recipient_name = recipient_name
    doc.custom_recipient_phone = recipient_phone
    doc.custom_delivery_address = delivery_address
    doc.custom_notes = notes

    for item in items:
        row = {"item_code": item["item_code"], "qty": item["qty"]}
        if item.get("rate"):        # لو مش مبعوت، ما نحطش المفتاح خالص — ERPNext يسعّر بنفسه
            row["rate"] = item["rate"]
        doc.append("items", row)

    doc.insert(ignore_permissions=True)
    doc.submit()

    return {"name": doc.name, "status": doc.status}
```

**ملاحظة:** المهمة دي محتاجة مهمة 1 (حقول Sales Order) تكون خلصت الأول، وإلا الدالة هتفشل
وقت الحفظ (حقول مش موجودة).

---

## قيود عامة لازم تلتزم بيها في كل المهام الثلاثة

- ما تعدلش أو تحذف أي حقل/دالة/fixture موجود حاليًا غير المذكور صراحة فوق.
- ما تشتغلش على بيانات حقيقية موجودة ولا تحذف أي سجل.
- لو أي مهمة فشلت، وقف عندها وابلغني بالمشكلة بالظبط — ما تكملش للمهمة اللي بعدها وما
  تحاولش تصلح المشكلة بطريقتك الخاصة.

## بعد الانتهاء

رد عليّ بحالة كل مهمة على حدة (تمت / فشلت ولماذا)، وقولّي رابط Laravel اللي استخدمته
فعليًا في `request_url` بمهمة 2.

## نهاية البرومبت

---

## سجل الحالة (تحدّثه إنت بعد كل رد من الـ AI التاني)

| # | المهمة | الحالة |
|---|---|---|
| 1 | حقول Item (`custom_is_featured`, `custom_featured_order`) | ⏳ لسه محتاج تأكيد |
| 1 | حقل Product Bundle (`custom_image`) | ⏳ لسه محتاج تأكيد |
| 1 | حقول Sales Order (التوصيل الأربعة) | ⏳ لسه محتاج تأكيد |
| 2 | الـ 3 Webhooks | ⏳ لسه محتاج تأكيد |
| 3 | تعديل `create_sales_order` | ⏳ لسه محتاج تأكيد |
