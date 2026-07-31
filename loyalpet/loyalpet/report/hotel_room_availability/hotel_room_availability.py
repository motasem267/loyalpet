import frappe
from frappe.utils import today, getdate


def execute(filters=None):
	filters = filters or {}
	check_date = getdate(filters.get("date") or today())

	columns = [
		{"label": "Room", "fieldname": "room_name", "fieldtype": "Link", "options": "Hotel Room", "width": 160},
		{"label": "Room Type", "fieldname": "room_type", "fieldtype": "Link", "options": "Hotel Room Type", "width": 160},
		{"label": "Status", "fieldname": "availability_status", "fieldtype": "Data", "width": 130},
		{"label": "Guest", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 160},
		{"label": "Booking", "fieldname": "booking_name", "fieldtype": "Link", "options": "Hotel Booking", "width": 160},
		{"label": "Check-in", "fieldname": "check_in_date", "fieldtype": "Date", "width": 110},
		{"label": "Check-out", "fieldname": "check_out_date", "fieldtype": "Date", "width": 110},
	]

	rooms = frappe.get_all(
		"Hotel Room",
		filters={"is_active": 1},
		fields=["name", "room_type"],
		order_by="name",
	)

	data = []
	for room in rooms:
		booking = frappe.db.get_value(
			"Hotel Booking",
			{
				"room": room.name,
				"check_in_date": ["<=", check_date],
				"check_out_date": [">=", check_date],
				"status": ["in", ["Confirmed", "Checked In"]],
			},
			["name", "customer", "check_in_date", "check_out_date", "status"],
			as_dict=True,
		)

		if booking:
			data.append({
				"room_name": room.name,
				"room_type": room.room_type,
				"availability_status": booking.status,
				"customer": booking.customer,
				"booking_name": booking.name,
				"check_in_date": booking.check_in_date,
				"check_out_date": booking.check_out_date,
			})
		else:
			data.append({
				"room_name": room.name,
				"room_type": room.room_type,
				"availability_status": "Available",
				"customer": None,
				"booking_name": None,
				"check_in_date": None,
				"check_out_date": None,
			})

	return columns, data
