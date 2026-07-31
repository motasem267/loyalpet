"""
Create a dedicated Role for the Laravel payment-gateway integration and assign
it to the integration user, so loyalpet.api.wallet.credit_wallet can be locked
down to that identity instead of trusting any authenticated user.
"""
import frappe

ROLE = "Wallet Payment Integration"
INTEGRATION_USER = "info@loyalpet.ly"


def execute():
	if not frappe.db.exists("Role", ROLE):
		frappe.get_doc({
			"doctype": "Role",
			"role_name": ROLE,
			"desk_access": 0,
		}).insert(ignore_permissions=True)

	if frappe.db.exists("User", INTEGRATION_USER):
		user = frappe.get_doc("User", INTEGRATION_USER)
		if not any(r.role == ROLE for r in user.roles):
			user.append("roles", {"role": ROLE})
			user.save(ignore_permissions=True)

	frappe.db.commit()
