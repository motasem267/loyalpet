import frappe
from frappe import _

STATE_UNDER_REVIEW = "قيد المراجعة"
STATE_OUT_FOR_DELIVERY = "قيد التوصيل"
STATE_PAYMENT_ERROR = "خطأ في عملية الدفع"


@frappe.whitelist()
def create_sales_order(customer_id, items, payment_method, recipient_name,
						recipient_phone, delivery_address, notes=None, delivery_date=None):
	"""
	إنشاء Sales Order من Laravel
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

	_process_payment(doc)

	return {"name": doc.name, "status": doc.status, "workflow_state": doc.custom_workflow_state}


def _process_payment(doc):
	if doc.custom_payment_method == "cash_on_delivery":
		doc.custom_workflow_state = STATE_OUT_FOR_DELIVERY

	elif doc.custom_payment_method == "wallet":
		# الخصم الفعلي بيحصل وقت الـ Sales Invoice (loyalpet.events.sales_invoice._charge_wallet)
		# هنا بس نتأكد إن الرصيد كافي عشان نقرر الحالة
		wallet = frappe.db.get_value("Wallet", {"customer": doc.customer}, ["name", "balance", "is_frozen"], as_dict=True)
		if not wallet or wallet.is_frozen or wallet.balance < doc.grand_total:
			doc.custom_workflow_state = STATE_PAYMENT_ERROR
		else:
			doc.custom_workflow_state = STATE_OUT_FOR_DELIVERY

	else:
		frappe.throw(_("طريقة دفع غير معروفة: {0}").format(doc.custom_payment_method))

	# كل الحالات الممكنة هنا (قيد التوصيل / خطأ في عملية الدفع) doc_status=1 في الـ Workflow
	doc.submit()
