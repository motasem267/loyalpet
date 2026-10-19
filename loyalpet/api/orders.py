import frappe
from frappe import _

from loyalpet.events.wallet import has_sufficient_balance
from loyalpet.events.webhook_utils import notify_webhook

STATE_UNDER_REVIEW = "قيد المراجعة"
STATE_CANCELLED = "ملغي"
SALES_ORDER_WEBHOOK = "LoyalPet Sales Order Sync"


@frappe.whitelist()
def create_sales_order(customer_id, items, payment_method, recipient_name,
						recipient_phone, delivery_address, notes=None, delivery_date=None):
	"""
	إنشاء Sales Order من Laravel — يتسجل "قيد المراجعة" وينتظر موافقة الموظف.
	الخصم الفعلي من المحفظة بيحصل بعدين وقت الفوترة، هنا بس فحص مبدئي للرصيد.
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
	_set_items(doc, items)

	doc.insert(ignore_permissions=True)
	# بعد insert عشان grand_total يكون محسوب — الـ throw بيعمل rollback للطلب كله
	_check_wallet_balance(doc)

	return {"name": doc.name, "status": doc.status, "workflow_state": doc.custom_workflow_state}


@frappe.whitelist()
def update_sales_order(name, customer_id, recipient_name=None, recipient_phone=None,
						delivery_address=None, delivery_date=None, notes=None,
						payment_method=None, items=None):
	"""
	تعديل طلب من الزبون وهو لسه "قيد المراجعة". أي حقل مش مبعوت (None) ما يتغيرش.
	items لو اتبعتت تكون القائمة كاملة بعد التعديل وبتستبدل الأصناف الحالية.
	POST /api/method/loyalpet.api.orders.update_sales_order
	"""
	doc = _get_editable_order(name, customer_id)

	updates = {
		"custom_recipient_name": recipient_name,
		"custom_recipient_phone": recipient_phone,
		"custom_delivery_address": delivery_address,
		"delivery_date": delivery_date,
		"custom_notes": notes,
		"custom_payment_method": payment_method,
	}
	for field, value in updates.items():
		if value is not None:
			doc.set(field, value)

	if items is not None:
		doc.set("items", [])
		_set_items(doc, items)

	doc.save(ignore_permissions=True)
	# بعد save عشان grand_total الجديد يكون محسوب — الـ throw بيعمل rollback للتعديل كله
	_check_wallet_balance(doc)

	return {
		"name": doc.name,
		"status": doc.status,
		"workflow_state": doc.custom_workflow_state,
		"grand_total": doc.grand_total,
		"items": [
			{"item_code": i.item_code, "qty": i.qty, "rate": i.rate, "amount": i.amount}
			for i in doc.items
		],
	}


@frappe.whitelist()
def cancel_sales_order(name, customer_id):
	"""
	إلغاء طلب من الزبون وهو لسه "قيد المراجعة". الطلب ما يتمسحش، يقعد مسجل بحالة "ملغي".
	POST /api/method/loyalpet.api.orders.cancel_sales_order
	"""
	_get_editable_order(name, customer_id, _("لا يمكن إلغاء الطلب بعد بدء تجهيزه"))
	_mark_cancelled(name)
	return {"name": name, "workflow_state": STATE_CANCELLED}


@frappe.whitelist()
def reject_sales_order(name):
	"""
	رفض طلب لسه "قيد المراجعة" (Draft).
	"""
	current_state = frappe.db.get_value("Sales Order", name, "custom_workflow_state")
	if current_state != STATE_UNDER_REVIEW:
		frappe.throw(_("الطلب مش في حالة قيد المراجعة (الحالة الحالية: {0})").format(current_state))

	_mark_cancelled(name)
	return {"name": name, "workflow_state": STATE_CANCELLED}


def _get_editable_order(name, customer_id, locked_message=None):
	"""الطلب لازم يكون تابع للزبون ولسه "قيد المراجعة" (Draft) — غير كده يترفض."""
	customer = frappe.db.get_value("Sales Order", name, "customer")
	if not customer or customer != customer_id:
		frappe.throw(_("الطلب غير موجود"), frappe.DoesNotExistError)

	doc = frappe.get_doc("Sales Order", name)
	# "قيد المراجعة" معرّفة في الـ Workflow بـ doc_status 0، فالطلب في الحالة دي
	# دايمًا Draft — فحص docstatus هنا احتياط بس.
	if doc.custom_workflow_state != STATE_UNDER_REVIEW or doc.docstatus != 0:
		frappe.throw(locked_message or _("لا يمكن تعديل الطلب بعد بدء تجهيزه"))
	return doc


def _set_items(doc, items):
	items = frappe.parse_json(items) if isinstance(items, str) else items
	if not items:
		frappe.throw(_("يجب أن يحتوي الطلب على صنف واحد على الأقل"))

	for item in items:
		row = {"item_code": item["item_code"], "qty": item["qty"]}
		if item.get("rate"):        # لو مش مبعوت، ما نحطش المفتاح خالص — ERPNext يسعّر بنفسه
			row["rate"] = item["rate"]
		doc.append("items", row)


def _check_wallet_balance(doc):
	if doc.custom_payment_method == "wallet" and not has_sufficient_balance(doc.customer, doc.grand_total):
		frappe.throw(_("الرصيد غير كافٍ في المحفظة"))


def _mark_cancelled(name):
	"""
	محرك الـ Workflow بتاع Frappe مش بيسمح بتعريف انتقال Draft->Cancelled خالص
	(بيرفض حفظ التعريف نفسه)، والـ Draft أصلًا ما ينفعش يتعمله doc.cancel().
	فالتحديث هنا بيحصل مباشرة على الداتابيز بدل ما يمر بـ doc.save()/apply_workflow،
	والطلب بيفضل متسجل بحالة "ملغي" بدل ما يتمسح.
	"""
	frappe.db.set_value("Sales Order", name, "custom_workflow_state", STATE_CANCELLED)
	frappe.db.commit()

	# db.set_value مش بيمر بـ doc.save() ومش بيفعّل الويب هوك لوحده — لازم نبلّغ
	# Laravel يدويًا بنفس الشكل اللي بيوصلها عادةً لما custom_workflow_state يتغيّر.
	notify_webhook(frappe.get_doc("Sales Order", name), SALES_ORDER_WEBHOOK)
