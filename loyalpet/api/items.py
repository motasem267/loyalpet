import json

import frappe
from frappe import _


@frappe.whitelist()
def get_items(limit_start=0, limit_page_length=500):
	"""مزامنة كاملة (pull) لكل المنتجات الموجودة في ERPNext — نفس شكل البيانات
	بالظبط اللي ويب هوكس الإضافة/التعديل بيبعتوها (doctype/name/item_code/
	item_name/item_group/description/image/standard_rate/disabled/
	has_variants/variant_of/attributes)، عشان لارافيل يقدر يعمل reconcile
	كامل (upsert لكل حاجة راجعة هنا) من غير ما يعتمد بس على الويب هوكس.
	بترجع كل الأصناف (مفعّلة وغير مفعّلة) مع pagination — استمر تنادي بزيادة
	limit_start لحد ما ترجعلك قائمة فاضية.
	"""
	items = frappe.get_all(
		"Item",
		fields=[
			"name", "item_code", "item_name", "item_group", "description", "image",
			"standard_rate", "disabled", "has_variants", "variant_of",
		],
		order_by="item_code asc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length),
	)
	if not items:
		return items

	names = [i.name for i in items]
	attr_rows = frappe.get_all(
		"Item Variant Attribute",
		filters={"parent": ["in", names]},
		fields=["parent", "attribute", "attribute_value"],
		order_by="idx asc",
	)
	attrs_by_item = {}
	for row in attr_rows:
		attrs_by_item.setdefault(row.parent, []).append(
			{"attribute": row.attribute, "attribute_value": row.attribute_value}
		)

	for i in items:
		i["doctype"] = "Item"
		i["attributes"] = attrs_by_item.get(i.name, [])

	return items


@frappe.whitelist()
def get_template_variant_prices(template):
	"""كل الـ variants بتاعة تمبلت معيّن مع سعر كل واحد وملخص خصائصه
	(الحجم/النكهة/اللون...)، عشان تتعرض في تاب "أسعار الأصناف"."""
	if not frappe.db.get_value("Item", template, "has_variants"):
		frappe.throw(_("{0} مش تمبلت (has_variants غير مفعّل)").format(template))

	variants = frappe.get_all(
		"Item",
		filters={"variant_of": template},
		fields=["name", "item_code", "item_name", "standard_rate"],
		order_by="item_code asc",
	)
	if not variants:
		return []

	variant_names = [v.name for v in variants]
	attr_rows = frappe.get_all(
		"Item Variant Attribute",
		filters={"parent": ["in", variant_names]},
		fields=["parent", "attribute", "attribute_value"],
		order_by="idx asc",
	)
	attrs_by_variant = {}
	for row in attr_rows:
		attrs_by_variant.setdefault(row.parent, []).append(f"{row.attribute}: {row.attribute_value}")

	for v in variants:
		v["attributes_label"] = " | ".join(attrs_by_variant.get(v.name, []))

	return variants


@frappe.whitelist()
def bulk_update_variant_prices(prices):
	"""prices: [{"item_code": "...", "rate": 12.5}, ...] — بتحدّث standard_rate
	لكل variant، والمزامنة مع Item Price (loyalpet.events.item.sync_item_price_from_standard_rate)
	بتتفعّل تلقائي لكل واحد زي أي حفظ عادي."""
	if isinstance(prices, str):
		prices = json.loads(prices)

	updated = []
	for row in prices:
		item_code = row.get("item_code")
		rate = row.get("rate")
		if not item_code or rate is None:
			continue

		rate = frappe.utils.flt(rate)
		if frappe.db.get_value("Item", item_code, "standard_rate") == rate:
			continue

		item = frappe.get_doc("Item", item_code)
		item.standard_rate = rate
		item.save()
		updated.append(item_code)

	frappe.db.commit()
	return {"updated": updated}
