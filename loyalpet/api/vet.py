import frappe
from frappe import _


@frappe.whitelist()
def create_vet_appointment(customer_id, service_type, appointment_date, appointment_time,
							doctor=None, notes=None):
	"""
	حجز موعد بيطري من Laravel
	POST /api/method/loyalpet.api.vet.create_vet_appointment
	"""
	if not frappe.db.exists("Customer", customer_id):
		frappe.throw(_("العميل غير موجود"), frappe.DoesNotExistError)
	if not frappe.db.exists("Vet Service Type", service_type):
		frappe.throw(_("نوع الخدمة البيطرية غير موجود"), frappe.DoesNotExistError)

	doc = frappe.new_doc("Vet Appointment")
	doc.customer = customer_id
	doc.service_type = service_type
	doc.appointment_date = appointment_date
	doc.appointment_time = appointment_time
	doc.doctor = doctor
	doc.notes = notes
	doc.insert(ignore_permissions=True)

	return {"name": doc.name, "status": doc.status, "total_amount": doc.total_amount}


@frappe.whitelist()
def get_vet_appointments(customer_id):
	"""
	كل المواعيد البيطرية الخاصة بعميل معيّن مع حالة كل موعد (الأحدث أولًا)
	POST /api/method/loyalpet.api.vet.get_vet_appointments
	"""
	if not frappe.db.exists("Customer", customer_id):
		frappe.throw(_("العميل غير موجود"), frappe.DoesNotExistError)

	return frappe.get_all(
		"Vet Appointment",
		filters={"customer": customer_id},
		fields=[
			"name", "service_type", "doctor", "appointment_date", "appointment_time",
			"status", "total_amount", "notes", "creation",
		],
		order_by="creation desc",
	)
