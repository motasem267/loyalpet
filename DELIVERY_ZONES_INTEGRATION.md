# تكامل "مناطق التوصيل" (Delivery Zones) — ERPNext ↔ Laravel

هذا التوثيق موجّه لمن يضيف دعم مناطق التوصيل في مشروع Laravel middleware
الخاص بـ LoyalPet. يشرح شكل البيانات، الـ API، وآلية الـ Webhook.

---

## 1. الفكرة العامة

أُضيف DocType جديد في ERPNext اسمه **Delivery Zone** — سجل بسيط لكل منطقة
توصيل واسمها وسعر التوصيل الخاص بها. الموظفين بيديروه من Desk (إضافة/تعديل/
تعطيل مناطق). لارافيل يحتاج:

1. **قراءة قائمة المناطق النشطة** (لعرضها للعميل عند اختيار التوصيل) — عبر API.
2. **استقبال أي تغيير يحصل في ERPNext تلقائيًا** (سعر تغيّر، منطقة جديدة
   اتضافت، منطقة اتعطّلت) — عبر Webhook، بدون الحاجة تستدعي الـ API كل مرة.

## 2. شكل البيانات (Delivery Zone)

| الحقل | النوع | ملاحظة |
|---|---|---|
| `name` | Data | معرّف ERPNext الفريد (autoname افتراضي، يُستخدم كـ ID) |
| `zone_name` | Data | اسم المنطقة (فريد، مطلوب) |
| `delivery_price` | Currency | سعر التوصيل لهذه المنطقة |
| `is_active` | Check (0/1) | هل المنطقة متاحة حاليًا |

## 3. الـ API (قراءة فقط)

**Method:** `loyalpet.api.delivery_zones.get_delivery_zones`
**Endpoint:** `POST /api/method/loyalpet.api.delivery_zones.get_delivery_zones`
**Auth:** نفس API key/secret المستخدمين حاليًا (`Authorization: token <api_key>:<api_secret>`)
**Body:** لا يحتاج أي بارامترات.

**مثال طلب:**
```bash
curl -X POST "https://dashboard.loyalpet.ly/api/method/loyalpet.api.delivery_zones.get_delivery_zones" \
  -H "Authorization: token <api_key>:<api_secret>"
```

**الرد** (مصفوفة، مرتبة أبجديًا باسم المنطقة، **المناطق النشطة فقط**):
```json
{
  "message": [
    {"name": "DZ-0001", "zone_name": "طرابلس المركز", "delivery_price": 15.0},
    {"name": "DZ-0002", "zone_name": "تاجوراء", "delivery_price": 20.0}
  ]
}
```

> ملاحظة: `name` هنا هو معرّف ERPNext (autoname) — استخدمه كـ `zone_id` لو
> محتاج تربط الطلب بمنطقة معيّنة عند إنشاء Sales Order.

## 4. الـ Webhook (إشعار تلقائي بأي تغيير)

نفس آلية باقي الـ webhooks الموجودة حاليًا (Item, Customer, Sales Order...):
POST على نفس الـ endpoint المشترك عندكم (`/api/v1/webhooks/erp`)، مع نفس
توقيع HMAC-SHA256 اللي بتتحققوا منه فعلًا لباقي الأحداث (نفس `webhook_secret`
المشترك، هيدر `X-Frappe-Webhook-Signature`).

**يوجد حدثين منفصلين:**

| متى يتفعّل | البيانات المرسلة |
|---|---|
| إنشاء منطقة جديدة | نفس الشكل تحت |
| تعديل منطقة موجودة (سعر، تفعيل/تعطيل، اسم) | نفس الشكل تحت |

**Payload:**
```json
{
  "doctype": "Delivery Zone",
  "name": "DZ-0002",
  "zone_name": "تاجوراء",
  "delivery_price": 20.0,
  "is_active": 1
}
```

**كيف تتعرفوا على نوع الحدث:** الـ endpoint المشترك عندكم بيميّز الحدث من
حقل `"doctype"` في الـ payload (زي ما بتعملوا مع باقي الأنواع Item/Customer/
إلخ). كل حركة على Delivery Zone (إنشاء أو تعديل) بتوصل بنفس شكل الـ payload
بالظبط أعلاه — الفرق الوحيد إن `is_active` ممكن يبقى `0` لو المنطقة اتعطّلت
(مش هيتحذف السجل، بس تجاهلوه من قوائم الاختيار).

## 5. التوصية للتكامل من جانب Laravel

1. **جدول محلي** يعكس نفس الحقول (`erp_zone_id`, `zone_name`, `delivery_price`,
   `is_active`) — يتحدّث من الـ webhook فورًا، ويُستخدم كـ cache محلي بدل
   استدعاء الـ API في كل طلب.
2. **أول مرة** (أو لو الجدول فاضي): نادوا `get_delivery_zones` عشان تعملوا
   seed أولي، بعدين اعتمدوا على الـ webhook للتحديثات التالية.
3. لو استقبلتوا webhook لمنطقة مش موجودة عندكم محليًا (نادرًا، مثلاً لو
   فاتكم webhook قديم) → اعملوا upsert بناءً على `name` (المعرّف من ERPNext)،
   نفس المنطق المتبع مع الـ Item sync.

## 6. اختبار سريع

جرّبنا الـ API والـ webhook فعليًا (إنشاء منطقة، تعديل سعرها، تعطيلها)
وأكّدنا إن الشكل أعلاه مطابق 100% لما بيوصل فعليًا — مفيش تخمين في التوثيق ده.
