import frappe
from frappe import _
from frappe.model.document import Document


class HotelBooking(Document):
	def validate(self):
		if self.check_out_date <= self.check_in_date:
			frappe.throw(_("Check Out Date must be after Check In Date"))

		self.total_nights = (
			frappe.utils.getdate(self.check_out_date)
			- frappe.utils.getdate(self.check_in_date)
		).days

		self._calculate_total()

	def _calculate_total(self):
		price_per_night = frappe.db.get_value(
			"Hotel Room Type",
			frappe.db.get_value("Hotel Room", self.room, "room_type"),
			"price_per_night"
		) or 0

		services_total = 0
		for row in self.services:
			price_per_day = frappe.db.get_value("Hotel Room Service", row.service, "price_per_day") or 0
			row.amount = price_per_day * self.total_nights
			services_total += row.amount

		self.total_amount = (price_per_night * self.total_nights) + services_total
