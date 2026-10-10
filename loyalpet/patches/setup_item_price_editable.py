"""
"Standard Selling Rate" في فورم Item كان يظهر وقت الإضافة بس
(depends_on: eval:doc.__islocal) ويختفي تلقائيًا بعد الحفظ — يعني مينفعش
نعدل بيه سعر منتج موجود من قبل. نشيل الشرط ده عشان الحقل يفضل ظاهر وقابل
للتعديل حتى بعد الحفظ. المزامنة مع Item Price
(loyalpet.events.item.sync_item_price_from_standard_rate) شغالة في
الحالتين (إضافة وتعديل) من قبل كده.
"""
import frappe


def execute():
	if frappe.db.exists(
		"Property Setter",
		{"doc_type": "Item", "field_name": "standard_rate", "property": "depends_on"},
	):
		return

	frappe.make_property_setter({
		"doctype": "Item",
		"fieldname": "standard_rate",
		"doctype_or_field": "DocField",
		"property": "depends_on",
		"value": "",
		"property_type": "Code",
	})

	frappe.clear_cache(doctype="Item")
	frappe.db.commit()
