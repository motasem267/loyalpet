import frappe


def cascade_disabled_to_variants(doc, method):
	"""لما Template يتفعّل/يتعطّل، نفس الحالة تتطبّق على كل الـ variants بتاعته
	(كل تعديل بيعمل save عادي، فالـ webhook الخاص بكل variant بيتفعّل لوحده)."""
	if not doc.has_variants:
		return
	if not doc.has_value_changed("disabled"):
		return

	variants = frappe.get_all(
		"Item", filters={"variant_of": doc.name, "disabled": ["!=", doc.disabled]}, pluck="name"
	)
	for variant_name in variants:
		variant = frappe.get_doc("Item", variant_name)
		variant.disabled = doc.disabled
		variant.save(ignore_permissions=True)
