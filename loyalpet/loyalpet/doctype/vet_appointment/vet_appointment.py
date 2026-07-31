import frappe
from frappe.model.document import Document


class VetAppointment(Document):
	def before_save(self):
		if self.service_type:
			self.total_amount = frappe.db.get_value("Vet Service Type", self.service_type, "price") or 0
