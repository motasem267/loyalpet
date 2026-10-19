import frappe
from frappe import _

from loyalpet.events.wallet import has_sufficient_balance
from loyalpet.events.webhook_utils import notify_webhook

STATE_UNDER_REVIEW = "قيد المراجعة"
STATE_AWAITING_TRANSFER = "بانتظار تأكيد الحوالة"
STATE_CANCELLED = "ملغي"
# الحالات اللي الزبون يقدر يعدّل ويلغي فيها (الاثنين Draft في الـ Workflow)
EDITABLE_STATES = (STATE_UNDER_REVIEW, STATE_AWAITING_TRANSFER)

PAYMENT_METHODS = ("cash_on_delivery", "wallet", "card_on_delivery", "bank_transfer")
BANK_TRANSFER = "bank_transfer"

SALES_ORDER_WEBHOOK = "LoyalPet Sales Order Sync"


@frappe.whitelist()
def create_sales_order(customer_id, items, payment_method, recipient_name,
						recipient_phone, delivery_address, notes=None, delivery_date=None,
						transfer_receipt=None):
	"""
	إنشاء Sales Order من Laravel — يتسجل "قيد المراجعة" وينتظر موافقة الموظف،
	ومع الحوالة يتسجل "بانتظار تأكيد الحوالة" لين الموظف يطابق الإيصال.
	الخصم الفعلي من المحفظة بيحصل بعدين وقت الفوترة، هنا بس فحص مبدئي للرصيد.
	POST /api/method/loyalpet.api.orders.create_sales_order
	"""
	if not frappe.db.exists("Customer", customer_id):
		frappe.throw(_("العميل غير موجود"), frappe.DoesNotExistError)
	_validate_payment_method(payment_method)

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
	if payment_method == BANK_TRANSFER:
		_set_transfer_receipt(doc, transfer_receipt)
	_set_items(doc, items)

	# الـ Workflow ما يسمحش بإنشاء مستند في حالة غير الأولى، فالطلب يتسجل
	# "قيد المراجعة" وبعدين ينقل للحوالة مباشرة على الداتابيز.
	doc.insert(ignore_permissions=True)
	# بعد insert عشان grand_total يكون محسوب — الـ throw بيعمل rollback للطلب كله
	_check_wallet_balance(doc)
	if payment_method == BANK_TRANSFER:
		# الويب هوك متاع الإنشاء لسه في الطابور (يطلع بعد الـ commit) وماسك نفس
		# الـ doc، فيطلع بالحالة الجديدة من غير ما نبعته مرة ثانية.
		_set_state(doc, STATE_AWAITING_TRANSFER, notify=False)

	return {"name": doc.name, "status": doc.status, "workflow_state": doc.custom_workflow_state}


@frappe.whitelist()
def update_sales_order(name, customer_id, recipient_name=None, recipient_phone=None,
						delivery_address=None, delivery_date=None, notes=None,
						payment_method=None, items=None, transfer_receipt=None):
	"""
	تعديل طلب من الزبون وهو لسه "قيد المراجعة" أو "بانتظار تأكيد الحوالة".
	أي حقل مش مبعوت (None) ما يتغيرش. items لو اتبعتت تكون القائمة كاملة بعد
	التعديل وبتستبدل الأصناف الحالية.
	POST /api/method/loyalpet.api.orders.update_sales_order
	"""
	doc = _get_editable_order(name, customer_id)
	if payment_method is not None:
		_validate_payment_method(payment_method)

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

	is_transfer = doc.custom_payment_method == BANK_TRANSFER
	if is_transfer and (transfer_receipt or not doc.custom_transfer_receipt):
		_set_transfer_receipt(doc, transfer_receipt)
	elif not is_transfer:
		# الملف نفسه يقعد في مرفقات الطلب، بس الطلب ما عادش حوالة
		doc.custom_transfer_receipt = None

	if items is not None:
		doc.set("items", [])
		_set_items(doc, items)

	doc.save(ignore_permissions=True)
	# بعد save عشان grand_total الجديد يكون محسوب — الـ throw بيعمل rollback للتعديل كله
	_check_wallet_balance(doc)

	# التنقل بين الحالتين حسب طريقة الدفع — آخر خطوة، بعد ما كل الفحوصات عدّت
	new_state = STATE_AWAITING_TRANSFER if is_transfer else STATE_UNDER_REVIEW
	if new_state != doc.custom_workflow_state:
		_set_state(doc, new_state, notify=True)

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
	إلغاء طلب من الزبون وهو لسه "قيد المراجعة" أو "بانتظار تأكيد الحوالة".
	الطلب ما يتمسحش، يقعد مسجل بحالة "ملغي".
	POST /api/method/loyalpet.api.orders.cancel_sales_order
	"""
	_get_editable_order(name, customer_id, _("لا يمكن إلغاء الطلب بعد بدء تجهيزه"))
	_mark_cancelled(name)
	return {"name": name, "workflow_state": STATE_CANCELLED}


@frappe.whitelist()
def reject_sales_order(name, reason=None):
	"""
	رفض طلب لسه "قيد المراجعة" أو "بانتظار تأكيد الحوالة" (Draft).
	رفض الحوالة لازم يكون معاه سبب، يتكتب في custom_rejection_reason ويوصل للزبون.
	"""
	current_state = frappe.db.get_value("Sales Order", name, "custom_workflow_state")
	if current_state not in EDITABLE_STATES:
		frappe.throw(_("الطلب مش في حالة قيد المراجعة (الحالة الحالية: {0})").format(current_state))
	if current_state == STATE_AWAITING_TRANSFER and not (reason or "").strip():
		frappe.throw(_("اكتب سبب رفض الحوالة"))

	if reason:
		frappe.db.set_value("Sales Order", name, "custom_rejection_reason", reason.strip())
	_mark_cancelled(name)
	return {"name": name, "workflow_state": STATE_CANCELLED}


def _get_editable_order(name, customer_id, locked_message=None):
	"""الطلب لازم يكون تابع للزبون ولسه في حالة قابلة للتعديل (Draft) — غير كده يترفض."""
	customer = frappe.db.get_value("Sales Order", name, "customer")
	if not customer or customer != customer_id:
		frappe.throw(_("الطلب غير موجود"), frappe.DoesNotExistError)

	doc = frappe.get_doc("Sales Order", name)
	# الحالتين معرّفين في الـ Workflow بـ doc_status 0، فالطلب فيهم دايمًا
	# Draft — فحص docstatus هنا احتياط بس. وبعد تأكيد الحوالة الفلوس اتسجلت
	# (Payment Entry)، فأي تعديل في المبلغ ولا إلغاء يحتاج تسوية من الموظف.
	if (doc.custom_workflow_state not in EDITABLE_STATES or doc.docstatus != 0
			or doc.custom_transfer_payment_entry):
		frappe.throw(locked_message or _("لا يمكن تعديل الطلب بعد بدء تجهيزه"))
	return doc


def _validate_payment_method(payment_method):
	if payment_method not in PAYMENT_METHODS:
		frappe.throw(_("طريقة الدفع غير مدعومة"))


def _set_transfer_receipt(doc, file_url):
	"""الإيصال لازم يكون ملف لارافيل رفعه قبل ولسه مش مربوط بمستند ثاني.
	الربط نفسه بالطلب (مرفقات الطلب) بيعمله Frappe تلقائيًا وقت الحفظ
	(attach_files_to_document) لأن الحقل نوعه Attach Image."""
	if not file_url:
		frappe.throw(_("يجب إرفاق صورة إيصال الحوالة"))

	files = frappe.get_all(
		"File", filters={"file_url": file_url}, fields=["attached_to_doctype", "attached_to_name"]
	)
	usable = any(
		not f.attached_to_name or (f.attached_to_doctype == "Sales Order" and f.attached_to_name == doc.name)
		for f in files
	)
	if not usable:
		frappe.throw(_("تعذر العثور على صورة الإيصال، يرجى إعادة رفعها"))

	doc.custom_transfer_receipt = file_url


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


def _set_state(doc, state, notify):
	"""تغيير الحالة بطلب من الزبون — مباشرة على الداتابيز، لأن الـ Workflow ما
	فيهوش انتقالات بين "قيد المراجعة" و"بانتظار تأكيد الحوالة" (الانتقال الوحيد
	المعرّف هو تأكيد الموظف للحوالة)."""
	frappe.db.set_value("Sales Order", doc.name, "custom_workflow_state", state)
	doc.custom_workflow_state = state
	if notify:
		notify_webhook(doc, SALES_ORDER_WEBHOOK)


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
