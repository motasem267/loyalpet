import frappe
from frappe.model.document import Document


class Wallet(Document):
	def validate(self):
		if self.balance < 0:
			frappe.throw(frappe._("Wallet balance cannot be negative"))
