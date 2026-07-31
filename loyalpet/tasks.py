import frappe


def send_appointment_reminders():
	tomorrow = frappe.utils.add_days(frappe.utils.today(), 1)
	appointments = frappe.get_all(
		"Vet Appointment",
		filters={"appointment_date": tomorrow, "status": ["in", ["Pending", "Confirmed"]]},
		pluck="name",
	)
	if not appointments:
		return

	webhook = frappe.db.get_value(
		"Webhook", {"name": "LoyalPet Vet Appointment Sync (Update)", "enabled": 1}, "name"
	)
	if not webhook:
		return

	for name in appointments:
		doc = frappe.get_doc("Vet Appointment", name)
		frappe.enqueue(
			"frappe.integrations.doctype.webhook.webhook.enqueue_webhook",
			doc=doc,
			webhook={"name": webhook},
			queue="default",
		)


def expire_vouchers():
	today = frappe.utils.now_datetime()
	frappe.db.set_value(
		"Voucher",
		{"status": "Available", "expires_at": ["<", today]},
		"status",
		"Expired",
	)
	frappe.db.commit()


def check_hotel_checkouts():
	today = frappe.utils.today()
	frappe.db.set_value(
		"Hotel Booking",
		{"status": "Checked In", "check_out_date": ["<=", today]},
		"status",
		"Checked Out",
	)
	frappe.db.commit()
