import frappe
from frappe import _


@frappe.whitelist()
def create_hotel_booking(customer_id, room, check_in_date, check_out_date, payment_method,
						services=None, notes=None):
	"""
	حجز فندقة/إيواء من Laravel
	POST /api/method/loyalpet.api.hotel.create_hotel_booking
	"""
	if not frappe.db.exists("Customer", customer_id):
		frappe.throw(_("العميل غير موجود"), frappe.DoesNotExistError)
	if not frappe.db.exists("Hotel Room", room):
		frappe.throw(_("الغرفة غير موجودة"), frappe.DoesNotExistError)

	doc = frappe.new_doc("Hotel Booking")
	doc.customer = customer_id
	doc.room = room
	doc.check_in_date = check_in_date
	doc.check_out_date = check_out_date
	doc.payment_method = payment_method
	doc.notes = notes

	for row in (services or []):
		doc.append("services", {"service": row["service"]})

	doc.insert(ignore_permissions=True)

	return {"name": doc.name, "status": doc.status, "total_amount": doc.total_amount}


@frappe.whitelist()
def get_hotel_bookings(customer_id):
	"""
	كل حجوزات الفندقة/الإيواء الخاصة بعميل معيّن مع حالة كل حجز (الأحدث أولًا)
	POST /api/method/loyalpet.api.hotel.get_hotel_bookings
	"""
	if not frappe.db.exists("Customer", customer_id):
		frappe.throw(_("العميل غير موجود"), frappe.DoesNotExistError)

	return frappe.get_all(
		"Hotel Booking",
		filters={"customer": customer_id},
		fields=[
			"name", "room", "check_in_date", "check_out_date", "total_nights",
			"status", "payment_method", "total_amount", "notes", "creation",
		],
		order_by="creation desc",
	)
