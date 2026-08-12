# تكامل "أحجام/نكهات المنتجات" (Item Variants) — ERPNext ↔ Laravel

هذا التوثيق موجّه لمن يضيف دعم المنتجات متعددة الأحجام/النكهات في مشروع
Laravel middleware الخاص بـ LoyalPet. لا يوجد أي API أو DocType جديد هنا —
هذا تحسين على الـ webhooks الموجودة أصلًا لـ Item و Sales Order.

---

## 1. الفكرة من ناحية ERPNext

منتج زي "أرز" ممكن يتباع بأكتر من حجم (نص كيلو، كيلو، 2 كيلو) و/أو أكتر من
نكهة (لمنتجات زي البروتين مثلاً). في ERPNext ده بيتعمل عن طريق:

- **Item "Template"**: صنف أساسي (`has_variants = 1`) مش بيتباع بنفسه مباشرة.
- **Item "Variant"**: صنف حقيقي منفصل بكوده وسعره وصورته الخاصة، مرتبط
  بالـ Template عن طريق حقل `variant_of`، وله قيمة محددة لكل خاصية
  (Attribute) زي الوزن والنكهة.

يعني "أرز - كيلو" و"أرز - 2 كيلو" صنفين منفصلين تمامًا (item_code مختلف،
سعر مختلف، مخزون مستقل)، بس الاتنين مرتبطين بنفس الـ Template الأساسي.

## 2. البيانات اللي بتوصل لـ Laravel (Item Sync webhooks)

نفس الـ 3 webhooks الموجودة أصلًا لـ Item، بس بحقول إضافية:

| Webhook | الحدث |
|---|---|
| `LoyalPet Item Sync (Create)` | صنف جديد (منتج عادي أو variant) |
| `LoyalPet Item Sync` | تعديل على صنف موجود |
| `LoyalPet Item Sync (Delete)` | **جديد** — حذف صنف |

**شكل الـ payload** (لصنف هو variant بحجم "كيلو" ونكهة "شوكولاتة"):
```json
{
  "doctype": "Item",
  "name": "PROT-1KG-CHOC",
  "item_code": "PROT-1KG-CHOC",
  "item_name": "بروتين - كيلو - شوكولاتة",
  "item_group": "مكملات غذائية",
  "description": "بروتين - كيلو - شوكولاتة",
  "image": null,
  "standard_rate": 250.0,
  "disabled": 0,
  "has_variants": 0,
  "variant_of": "PROT-TEMPLATE",
  "attributes": [
    {"attribute": "الوزن", "attribute_value": "كيلو"},
    {"attribute": "النكهة", "attribute_value": "شوكولاتة"}
  ]
}
```

**ملاحظتين مهمتين عن `attributes`:**
- كل عنصر فيها فيه حقول Frappe داخلية زيادة (`creation`, `owner`, `idx`, إلخ) —
  **تجاهلوها تمامًا**، اللي يهمكم بس `attribute` و `attribute_value`.
- منتج عادي (مش variant) هيوصله `attributes: []` (مصفوفة فاضية) و
  `variant_of: null` — يعني نفس شكل الـ payload القديم بالظبط، محدش هيتكسر.

**صنف عادي (مش variant، مش template)** — نفس الشكل القديم، بس بحقول إضافية فاضية/صفرية:
```json
{
  "doctype": "Item", "name": "ITEM-001", "item_code": "ITEM-001",
  "item_name": "...", "item_group": "...", "description": "...",
  "image": "...", "standard_rate": 50.0, "disabled": 0,
  "has_variants": 0, "variant_of": null, "attributes": []
}
```

### `has_variants` — مهم جدًا لمنطق العرض/الطلب

لما `has_variants = 1`، معناه الصنف ده **Template فقط** (زي "أرز" الأساسي) —
**ERPNext نفسه بيرفض تمامًا** إنه يتباع أو يتحط في Sales Order مباشرة. لازم
Laravel:
- **متعرضوش الـ Template كمنتج قابل للطلب** — اعرضوه كـ "بطاقة اختيار" بس
  (زي "أرز" وتحته أزرار الأحجام)، والطلب الفعلي يبعت كود الـ **variant**
  المختار، مش كود الـ Template.
- Template بيوصلكوا بـ `has_variants: 1` و `variant_of: null` دايمًا (هو مش
  variant لحاجة، هو الأصل).
- أي صنف تاني (variant أو منتج عادي مالوش variants) بيوصل `has_variants: 0`.

**payload الحذف** (مختصر عمدًا، الغرض بس معرفة إيه اللي اتحذف):
```json
{"doctype": "Item", "name": "PROT-1KG-CHOC", "item_code": "PROT-1KG-CHOC"}
```

## 3. توصية بنية البيانات في Laravel

- **جدول `products`** (المنتجات الفعلية القابلة للبيع = كل الـ variants +
  المنتجات العادية اللي مالهاش variants) — كل صف فيه `erp_item_code`,
  `name`, `price`, `variant_of` (nullable), وجدول فرعي أو JSON column
  للـ `attributes`.
- لو `variant_of` موجود → اعرضوا المنتج كـ "خيار" تحت المنتج الأساسي
  (اللي هو نفسه `variant_of` كـ item_code) بدل ما يظهر كمنتج مستقل في
  القائمة الرئيسية. يعني في شاشة "أرز" مثلاً، تعرضوا اختيار الحجم
  (نص كيلو / كيلو / 2 كيلو) كأزرار تحت نفس المنتج، مش 3 منتجات منفصلة.
- **الحذف**: لما يوصل `LoyalPet Item Sync (Delete)`، متمسحوش الصف نهائي لو
  عنده تاريخ طلبات قديمة — الأفضل soft-delete (`is_active = false` أو
  عمود `deleted_at`) عشان الطلبات القديمة تفضل واضحة.

## 4. تفاصيل الأصناف داخل الطلب (Sales Order webhook)

`LoyalPet Sales Order Sync` بقى بيبعت قائمة الأصناف كاملة، مش الإجمالي بس:

```json
{
  "doctype": "Sales Order",
  "name": "SAL-ORD-2026-00016",
  "customer": "CUST-2026-00003",
  "grand_total": 60.0,
  "custom_workflow_state": "قيد التوصيل",
  "custom_payment_method": "cash_on_delivery",
  "items": [
    {
      "item_code": "PROT-1KG-CHOC",
      "item_name": "بروتين - كيلو - شوكولاتة",
      "qty": 2.0,
      "rate": 30.0,
      "amount": 60.0
    }
  ]
}
```
`item_name` هنا بيحمل تفاصيل الحجم/النكهة تلقائيًا (لأنه اسم الـ variant
نفسه)، يعني تقدروا تعرضوا "بروتين - كيلو - شوكولاتة × 2" في تفاصيل الطلب
من غير ما تحتاجوا تربطوه بجدول الـ attributes تاني. زي `attributes`، كل
عنصر في `items` فيه حقول Frappe داخلية زيادة (`idx`, `parent`, إلخ) —
اعتمدوا بس على `item_code`, `item_name`, `qty`, `rate`, `amount`.

## 5. اختبار

اتعمل اختبار حقيقي (مش تخمين): إنشاء Template بخاصيتين (وزن + نكهة)،
توليد variant فعلي، وطلب Sales Order عليه — والـ payloads اللي فوق منسوخة
حرفيًا من نتيجة الاختبار ده.
