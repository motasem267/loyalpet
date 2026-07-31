import frappe


def run():
	c = frappe.new_doc("Customer")
	c.customer_name = "__Test AutoWallet Customer__"
	c.insert(ignore_permissions=True)

	exists = frappe.db.exists("Wallet", c.name)
	print("Customer:", c.name, "| Wallet exists with same name?:", exists)

	if exists:
		w = frappe.get_doc("Wallet", c.name)
		print("Wallet balance:", w.balance, "| currency:", w.currency, "| is_frozen:", w.is_frozen)

	# idempotency: re-trigger the hook manually shouldn't duplicate/error
	from loyalpet.events.customer import on_customer_created
	on_customer_created(c, "after_insert")
	print("Second call did not error (idempotent)")

	frappe.db.rollback()
	print("ROLLED BACK")
