"""
إظهار "Standard Selling Rate" في نافذة "+ New Item" السريعة (quick entry) —
عشان الموظف يقدر يحدد سعر البيع وهو بيضيف المنتج في خطوة واحدة، بدل ما
يضيف المنتج الأول وبعدين يروح لـ Price List يضيف السعر بشكل منفصل.
"""
import frappe


def execute():
	if frappe.db.exists(
		"Property Setter",
		{"doc_type": "Item", "field_name": "standard_rate", "property": "allow_in_quick_entry"},
	):
		return

	frappe.make_property_setter({
		"doctype": "Item",
		"fieldname": "standard_rate",
		"doctype_or_field": "DocField",
		"property": "allow_in_quick_entry",
		"value": "1",
		"property_type": "Check",
	})

	frappe.clear_cache(doctype="Item")
	frappe.db.commit()
