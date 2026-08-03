import frappe
from frappe import _

STATE_UNDER_REVIEW = "قيد المراجعة"
STATE_CANCELLED = "ملغي"


@frappe.whitelist()
def create_sales_order(customer_id, items, payment_method, recipient_name,
						recipient_phone, delivery_address, notes=None, delivery_date=None):
	"""
	إنشاء Sales Order من Laravel — يتسجل "قيد المراجعة" وينتظر موافقة الموظف.
	الدفع (كاش/محفظة) بيتعالج بعدين وقت الفوترة، مش هنا.
	POST /api/method/loyalpet.api.orders.create_sales_order
	"""
	if not frappe.db.exists("Customer", customer_id):
		frappe.throw(_("العميل غير موجود"), frappe.DoesNotExistError)

	doc = frappe.new_doc("Sales Order")
	doc.customer = customer_id
	doc.delivery_date = delivery_date or frappe.utils.add_days(frappe.utils.today(), 3)
	doc.order_type = "Sales"
	doc.custom_from_app = 1
	doc.custom_payment_method = payment_method
	doc.custom_recipient_name = recipient_name
	doc.custom_recipient_phone = recipient_phone
	doc.custom_delivery_address = delivery_address
	doc.custom_notes = notes
	doc.custom_workflow_state = STATE_UNDER_REVIEW

	for item in items:
		row = {"item_code": item["item_code"], "qty": item["qty"]}
		if item.get("rate"):        # لو مش مبعوت، ما نحطش المفتاح خالص — ERPNext يسعّر بنفسه
			row["rate"] = item["rate"]
		doc.append("items", row)

	doc.insert(ignore_permissions=True)

	return {"name": doc.name, "status": doc.status, "workflow_state": doc.custom_workflow_state}


@frappe.whitelist()
def reject_sales_order(name):
	"""
	رفض طلب لسه "قيد المراجعة" (Draft).
	محرك الـ Workflow بتاع Frappe مش بيسمح بتعريف انتقال Draft->Cancelled خالص
	(بيرفض حفظ التعريف نفسه)، فالتحديث هنا بيحصل مباشرة على الداتابيز بدل
	ما يمر بـ doc.save()/apply_workflow.
	"""
	current_state = frappe.db.get_value("Sales Order", name, "custom_workflow_state")
	if current_state != STATE_UNDER_REVIEW:
		frappe.throw(_("الطلب مش في حالة قيد المراجعة (الحالة الحالية: {0})").format(current_state))

	frappe.db.set_value("Sales Order", name, "custom_workflow_state", STATE_CANCELLED)
	frappe.db.commit()

	return {"name": name, "workflow_state": STATE_CANCELLED}
