import frappe

COMPANY = "LoyalPet"


def _bulk_delete(doctype, filters=None):
	f = filters if filters is not None else {"company": COMPANY}
	names = frappe.get_all(doctype, filters=f, pluck="name")
	if not names:
		print(f"  {doctype}: لا يوجد شيء")
		return
	print(f"  {doctype}: حذف {len(names)} سجل...", flush=True)
	# Cancel submitted docs directly in DB to bypass workflow checks
	table = f"tab{doctype}"
	frappe.db.sql(f"UPDATE `{table}` SET docstatus=2 WHERE name IN %(names)s", {"names": names})
	frappe.db.commit()
	for name in names:
		try:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True, delete_permanently=True)
		except Exception as e:
			print(f"    خطأ {name}: {e}")
	frappe.db.commit()


def run():
	# 1. GL + Payment Ledger + Stock Ledger مباشرة من DB
	print("[1] GL Entries + Payment Ledger...")
	n = frappe.db.count("GL Entry", {"company": COMPANY})
	frappe.db.delete("GL Entry", {"company": COMPANY})
	frappe.db.delete("Payment Ledger Entry", {"company": COMPANY})
	frappe.db.commit()
	print(f"    {n} سجل")

	print("[2] Stock Ledger Entries...")
	n = frappe.db.count("Stock Ledger Entry", {"company": COMPANY})
	frappe.db.delete("Stock Ledger Entry", {"company": COMPANY})
	frappe.db.commit()
	print(f"    {n} سجل")

	# 2. المستندات المالية بالترتيب
	for dt in [
		"Payment Entry",
		"Sales Invoice",
		"Delivery Note",
		"Sales Order",
		"Purchase Invoice",
		"Purchase Receipt",
		"Purchase Order",
		"Journal Entry",
		"Stock Entry",
	]:
		_bulk_delete(dt)

	# 3. Wallet Transactions + reset balances
	print("[3] Wallet Transactions + reset balances...")
	frappe.db.delete("Wallet Transaction", {})
	frappe.db.sql("UPDATE `tabWallet` SET balance = 0")
	frappe.db.commit()

	# 4. Items
	print("[4] Items...")
	items = frappe.get_all("Item", pluck="name")
	print(f"    {len(items)} منتج")
	for name in items:
		try:
			frappe.delete_doc("Item", name, force=True, ignore_permissions=True, delete_permanently=True)
		except Exception as e:
			print(f"    خطأ {name}: {e}")
	frappe.db.commit()

	# 5. Bin reset (مستودعات)
	print("[5] Bin reset...")
	frappe.db.sql(
		"UPDATE `tabBin` SET actual_qty=0, reserved_qty=0, ordered_qty=0,"
		" indented_qty=0, planned_qty=0, projected_qty=0"
	)
	frappe.db.commit()

	print("\nانتهى الحذف بنجاح!")
