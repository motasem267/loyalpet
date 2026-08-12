"""
1) اعرض اسم العميل بدل الـ ID بتاعه في أي مكان Customer مرتبط فيه (Link field)
   — Sales Order, Sales Invoice, Wallet, Wallet Transaction, إلخ.
2) رتّب قوائم الطلبات والفواتير بتاريخ الإنشاء (الأحدث أولًا)، بدل "آخر تعديل"
   اللي كان بيطلع سجلات قديمة اتعدّلت فوق سجلات جديدة لسه محدش لمسها.
"""
import frappe


def _set_property(doctype, property, value, property_type):
	if frappe.db.exists("Property Setter", {"doc_type": doctype, "property": property, "field_name": None}):
		return
	frappe.make_property_setter({
		"doctype": doctype,
		"doctype_or_field": "DocType",
		"property": property,
		"value": value,
		"property_type": property_type,
	})


def execute():
	_set_property("Customer", "show_title_field_in_link", "1", "Check")

	for doctype in ["Sales Order", "Sales Invoice"]:
		_set_property(doctype, "sort_field", "creation", "Data")
		_set_property(doctype, "sort_order", "DESC", "Select")

	frappe.clear_cache()
	frappe.db.commit()
