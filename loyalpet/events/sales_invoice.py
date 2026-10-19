import frappe
from frappe import _
from frappe.utils import flt

from loyalpet.events.wallet import has_sufficient_balance

# طريقة الدفع على الطلب -> Mode of Payment، والحساب يتجاب من إعداد طريقة الدفع
# نفسها باش الحسابات تفرّق بين النقدي والبطاقة والحوالة.
PAYMENT_MODE_MAP = {
	"wallet": "E-Wallet",
	"cash_on_delivery": "Cash",
	"card_on_delivery": "بطاقة",
	"bank_transfer": "حوالة",
}

STATE_COMPLETED = "مكتملة"
STATE_PAYMENT_ERROR = "خطأ في عملية الدفع"


def before_validate(doc, method):
	_allocate_transfer_advances(doc)


def _allocate_transfer_advances(doc):
	"""فلوس الحوالة اتسجلت دفعة مقدمة وقت تأكيدها (loyalpet.overrides.sales_order).
	هني تتخصم من الفاتورة، قبل validate عشان ERPNext يحسب outstanding_amount
	على أساسها. بنختار بس الدفعة المربوطة بالطلب نفسه، مش أي دفعة مقدمة
	تانية على الزبون (ممكن تكون متاعة طلب ثاني)."""
	if doc.is_return or doc.docstatus == 2 or not doc.debit_to:
		return

	orders = {item.sales_order for item in doc.items if item.sales_order}
	payment_entries = {
		pe for pe in (
			frappe.db.get_value("Sales Order", so, "custom_transfer_payment_entry") for so in orders
		) if pe
	}
	if not payment_entries:
		return

	other_rows = [r for r in doc.get("advances") if r.reference_name not in payment_entries]
	doc.set("advances", other_rows)

	remaining = (doc.get("rounded_total") or doc.grand_total) - sum(flt(r.allocated_amount) for r in other_rows)
	for entry in doc.get_advance_entries():
		if entry.reference_type != "Payment Entry" or entry.reference_name not in payment_entries:
			continue
		allocated = min(remaining, flt(entry.amount))
		remaining -= allocated
		doc.append("advances", {
			"reference_type": entry.reference_type,
			"reference_name": entry.reference_name,
			"reference_row": entry.reference_row,
			"remarks": entry.remarks,
			"advance_amount": flt(entry.amount),
			"allocated_amount": allocated,
			"ref_exchange_rate": flt(entry.exchange_rate),
			"difference_posting_date": doc.posting_date,
			"account": entry.get("paid_from"),
		})


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
	if doc.is_return:
		return

	# لو outstanding صفر (زي الحوالة المخصومة كدفعة مقدمة) الفاتورة خالصة
	# وما فيش دفع جديد يتسجل، بس الطلب برضه يكمل.
	if doc.outstanding_amount > 0:
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
	return has_sufficient_balance(doc.customer, doc.grand_total)


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
	from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account

	mode_of_payment = PAYMENT_MODE_MAP.get(payment_method, "Cash")
	pe = get_payment_entry("Sales Invoice", doc.name, party_amount=doc.outstanding_amount)
	pe.mode_of_payment = mode_of_payment
	pe.paid_to = get_bank_cash_account(mode_of_payment, doc.company)["account"]
	pe.reference_no = doc.name
	pe.reference_date = doc.posting_date
	pe.remarks = f"Auto-payment for {doc.name} via {payment_method}"
	pe.flags.ignore_permissions = True
	pe.insert()
	pe.submit()
