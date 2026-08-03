import frappe

TRACKED_PRICE_LIST = "Standard Selling"


def sync_standard_rate(doc, method):
	if doc.price_list != TRACKED_PRICE_LIST:
		return
	if doc.customer or doc.supplier:
		return  # سعر خاص بعميل/مورد معيّن، مش السعر العام اللي التطبيق بيعرضه

	item = frappe.get_doc("Item", doc.item_code)
	if item.standard_rate == doc.price_list_rate:
		return

	item.standard_rate = doc.price_list_rate
	item.save(ignore_permissions=True)
