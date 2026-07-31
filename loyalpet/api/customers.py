import frappe
from frappe import _


@frappe.whitelist()
def create_customer(app_user_id, name, phone=None, address=None):
	"""
	إنشاء أو استرجاع Customer من Laravel (idempotent على custom_app_user_id)
	POST /api/method/loyalpet.api.customers.create_customer
	"""
	existing = frappe.db.get_value("Customer", {"custom_app_user_id": app_user_id}, "name")
	if existing:
		return {"name": existing, "created": False}

	doc = frappe.new_doc("Customer")
	doc.customer_name = name
	doc.custom_app_user_id = app_user_id
	doc.custom_phone = phone
	doc.custom_address = address
	doc.insert(ignore_permissions=True)

	return {"name": doc.name, "created": True}
