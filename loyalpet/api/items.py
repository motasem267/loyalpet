import json

import frappe
from frappe import _


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
