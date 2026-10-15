import frappe

from loyalpet.events.webhook_utils import notify_webhook

TRACKED_PRICE_LIST = "Standard Selling"


def notify_rename(doc, method, old_name, new_name, merge=False):
	"""نفس مشكلة Item Group بالظبط — autoname بتاع Item مبني على item_code
	(field:)، فتغيير الكود من الديسك rename مش save، ومابيفعّلش on_update."""
	notify_webhook(doc, "LoyalPet Item Sync")


def sync_item_price_from_standard_rate(doc, method):
	"""لما الموظف يكتب "Standard Selling Rate" في نفس صفحة/نافذة إضافة المنتج،
	نعكس القيمة دي تلقائيًا كسجل Item Price حقيقي (نفس الحقل اللي بيستخدمه
	Sales Order/Invoice فعليًا للتسعير) — بدل ما يحتاج يروح Price List بشكل منفصل.
	عكس اتجاه loyalpet.events.item_price.sync_standard_rate، وبينهم حماية من التكرار
	اللا-منتهي: كل واحد بيوقف لو القيمتين متطابقتين فعلاً."""
	if not doc.standard_rate:
		return

	# ملاحظة: مش بنفلتر customer/supplier في الكويري نفسه — SQL's IN مايطابقش
	# NULL خالص (محتاج IS NULL صريح)، فكان بيفشل يلاقي السجل الموجود ويحاول
	# يضيف واحد جديد فوقه (duplicate). الفلترة هنا في بايثون أسلم وأوضح.
	rows = frappe.get_all(
		"Item Price",
		filters={"item_code": doc.name, "price_list": TRACKED_PRICE_LIST},
		fields=["name", "price_list_rate", "customer", "supplier"],
	)
	existing = next((row for row in rows if not row.customer and not row.supplier), None)

	if existing:
		if existing.price_list_rate == doc.standard_rate:
			return
		frappe.db.set_value("Item Price", existing.name, "price_list_rate", doc.standard_rate)
	else:
		frappe.get_doc({
			"doctype": "Item Price",
			"item_code": doc.name,
			"price_list": TRACKED_PRICE_LIST,
			"price_list_rate": doc.standard_rate,
			"currency": frappe.db.get_value("Price List", TRACKED_PRICE_LIST, "currency") or frappe.defaults.get_global_default("currency"),
		}).insert(ignore_permissions=True)


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
