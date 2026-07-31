"""
Set update_stock = 1 as default on Sales Invoice.
Stock deduction happens on invoice submit (no Delivery Note needed).
"""
import frappe


def execute():
	if frappe.db.exists(
		"Property Setter",
		{"doc_type": "Sales Invoice", "field_name": "update_stock", "property": "default"},
	):
		return  # Already applied

	frappe.make_property_setter({
		"doctype": "Sales Invoice",
		"fieldname": "update_stock",
		"property": "default",
		"value": "1",
		"property_type": "Check",
	})
	frappe.db.commit()
