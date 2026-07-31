import frappe

def run():
	so = frappe.get_doc("Sales Order", "SAL-ORD-2026-00003")
	so.customer = "محمد بن سعيد"
	so.flags.ignore_permissions = True
	so.save()

	frappe.delete_doc("Customer", "CUST-2026-00004", ignore_permissions=True, force=True)
	frappe.db.commit()
	print("REVERTED_SO_AND_DELETED_TEST_CUSTOMER")
