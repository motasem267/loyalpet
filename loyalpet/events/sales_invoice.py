import frappe
from frappe import _

PAYMENT_ACCOUNT_MAP = {
	"wallet": "E-Wallet - LP",
	"cash_on_delivery": "Cash - LP",
}

STATE_COMPLETED = "مكتملة"
STATE_PAYMENT_ERROR = "خطأ في عملية الدفع"


def validate(doc, method):
	_check_one_invoice_per_order(doc)
	for item in doc.items:
		if not item.sales_order:
			continue
		state = frappe.db.get_value("Sales Order", item.sales_order, "custom_workflow_state")
		if state != "تم الاستلام":
			frappe.throw(
				_("Sales Order {0} must be in تم الاستلام state before creating an invoice (current state: {1}).").format(
					frappe.bold(item.sales_order), frappe.bold(state or "Unknown")
				)
			)

	# لازم يتفحص هنا (قبل أي كتابة فعلية للفاتورة نفسها) عشان لو الرصيد مش
	# كافي نقدر نحدّث حالة الطلب ونعمل commit من غير ما نسيب أي أثر جزئي
	# للفاتورة نفسها (زي قيود مخزون/حسابات) بعد ما نرفض التسليم.
	if doc.docstatus == 1 and doc.outstanding_amount > 0:
		payment_method = _get_payment_method(doc)
		if payment_method == "wallet" and not _wallet_has_sufficient_balance(doc):
			_set_linked_orders_state(doc, STATE_PAYMENT_ERROR)
			# لازم commit هنا: هنعمل throw بعدها على طول، ولسه مفيش أي كتابة
			# فعلية للفاتورة نفسها حصلت (احنا لسه في validate) فمفيش خطر
			# نكمّت حاجة ناقصة أو نصفها.
			frappe.db.commit()
			frappe.throw(_("رصيد المحفظة غير كافٍ لإتمام الدفع"))


def _check_one_invoice_per_order(doc):
	seen = set()
	for item in doc.items:
		if not item.sales_order or item.sales_order in seen:
			continue
		seen.add(item.sales_order)

		existing = frappe.db.sql("""
			SELECT sii.parent
			FROM `tabSales Invoice Item` sii
			JOIN `tabSales Invoice` si ON si.name = sii.parent
			WHERE sii.sales_order = %s
			  AND si.docstatus != 2
			  AND sii.parent != %s
			LIMIT 1
		""", (item.sales_order, doc.name or "NEW"), as_dict=True)

		if existing:
			frappe.throw(
				_("Sales Order {0} already has a Sales Invoice: {1}. Each order can only have one invoice.").format(
					frappe.bold(item.sales_order), frappe.bold(existing[0].parent)
				)
			)


def on_submit(doc, method):
	if doc.outstanding_amount <= 0:
		return

	payment_method = _get_payment_method(doc)

	if payment_method == "wallet":
		# الرصيد اتأكد منه فعلًا في validate() — هنا الخصم الحقيقي، ومحمي كمان
		# ذرّيًا (row lock) جوه loyalpet.events.wallet لو حصل تغيّر لحظي في الرصيد
		_charge_wallet(doc)

	_create_payment_entry(doc, payment_method)
	_set_linked_orders_state(doc, STATE_COMPLETED)


def _get_payment_method(doc):
	for item in doc.items:
		if item.sales_order:
			method = frappe.db.get_value("Sales Order", item.sales_order, "custom_payment_method")
			if method:
				return method
	return "cash_on_delivery"


def _set_linked_orders_state(doc, state):
	seen = set()
	for item in doc.items:
		if not item.sales_order or item.sales_order in seen:
			continue
		seen.add(item.sales_order)
		frappe.db.set_value("Sales Order", item.sales_order, "custom_workflow_state", state)


def _wallet_has_sufficient_balance(doc):
	wallet = frappe.db.get_value("Wallet", doc.customer, ["balance", "is_frozen"], as_dict=True)
	if not wallet or wallet.is_frozen:
		return False
	return wallet.balance >= doc.grand_total


def _charge_wallet(doc):
	# Idempotency guard
	if frappe.db.exists("Wallet Transaction", {"reference": doc.name, "source": "order_payment"}):
		return

	wallet = frappe.get_doc("Wallet", doc.customer)

	# الخصم الفعلي وتحديث balance_before/balance_after بيحصل جوه
	# loyalpet.events.wallet.validate عند insert الـ Wallet Transaction دي
	frappe.get_doc({
		"doctype": "Wallet Transaction",
		"wallet": wallet.name,
		"customer": doc.customer,
		"type": "debit",
		"amount": doc.grand_total,
		"source": "order_payment",
		"reference": doc.name,
		"status": "Completed",
	}).insert(ignore_permissions=True)


def _create_payment_entry(doc, payment_method):
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	paid_to = PAYMENT_ACCOUNT_MAP.get(payment_method, "Cash - LP")
	pe = get_payment_entry("Sales Invoice", doc.name, party_amount=doc.outstanding_amount)
	pe.paid_to = paid_to
	pe.reference_no = doc.name
	pe.reference_date = doc.posting_date
	pe.remarks = f"Auto-payment for {doc.name} via {payment_method}"
	pe.flags.ignore_permissions = True
	pe.insert()
	pe.submit()
