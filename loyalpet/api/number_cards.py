import frappe
from frappe.utils import today


@frappe.whitelist()
def get_today_vet_appointments():
	return frappe.db.count("Vet Appointment", {"appointment_date": today()})


@frappe.whitelist()
def get_today_hotel_checkins():
	return frappe.db.count("Hotel Booking", {"check_in_date": today()})


@frappe.whitelist()
def get_available_rooms_today():
	total = frappe.db.count("Hotel Room", {"is_active": 1})
	occupied = frappe.db.count("Hotel Booking", {
		"check_in_date": ["<=", today()],
		"check_out_date": [">=", today()],
		"status": ["in", ["Confirmed", "Checked In"]],
	})
	return max(total - occupied, 0)
