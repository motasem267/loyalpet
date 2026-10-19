import frappe
from frappe import _
from frappe.utils import flt


class InsufficientWalletBalance(frappe.ValidationError):
	pass


def has_sufficient_balance(customer, amount):
	"""فحص مبدئي للرصيد (من غير خصم) — مستخدم وقت إنشاء/تعديل الطلب ووقت الفوترة.
	الخصم الفعلي محمي ذرّيًا في validate تحت."""
	wallet = frappe.db.get_value("Wallet", customer, ["balance", "is_frozen"], as_dict=True)
	if not wallet or wallet.is_frozen:
		return False
	return flt(wallet.balance) >= flt(amount)


def validate(doc, method):
	if not doc.is_new():
		frappe.throw(_("Wallet Transactions are immutable and cannot be modified."))
		return

	if flt(doc.amount) <= 0:
		frappe.throw(_("قيمة العملية يجب أن تكون أكبر من صفر"))

	wallet = frappe.db.get_value(
		"Wallet", doc.wallet, ["balance", "is_frozen", "customer"], as_dict=True, for_update=True
	)
	if wallet is None:
		frappe.throw(_("Wallet not found"))
	if doc.customer and doc.customer != wallet.customer:
		frappe.throw(_("المحفظة لا تخص هذا العميل"))
	doc.customer = wallet.customer
	balance_before = wallet.balance

	if doc.type == "debit":
		if wallet.is_frozen:
			frappe.throw(_("المحفظة مجمّدة"))
		balance_after = balance_before - doc.amount
		if balance_after < 0:
			frappe.throw(_("رصيد المحفظة غير كافٍ"), InsufficientWalletBalance)
	else:
		balance_after = balance_before + doc.amount

	doc.balance_before = balance_before
	doc.balance_after = balance_after
	frappe.db.set_value("Wallet", doc.wallet, "balance", balance_after)


def on_trash(doc, method):
	frappe.throw(_("Wallet Transactions cannot be deleted."))
