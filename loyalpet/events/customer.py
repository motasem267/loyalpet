import frappe


def on_customer_created(doc, method):
	if frappe.db.exists("Wallet", doc.name):
		return

	frappe.get_doc({
		"doctype": "Wallet",
		"customer": doc.name,
	}).insert(ignore_permissions=True)
