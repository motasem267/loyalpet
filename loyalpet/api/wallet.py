import frappe
from frappe import _
from frappe.utils import flt

MANUAL_ADJUSTMENT_ROLES = ("System Manager", "Sales Manager")
PAYMENT_INTEGRATION_ROLE = "Wallet Payment Integration"


@frappe.whitelist()
def credit_wallet(erp_customer_id, amount, reference):
	"""
	شحن محفظة العميل بعد تأكيد الدفع من بوابة الدفع (Laravel)
	POST /api/method/loyalpet.api.wallet.credit_wallet

	idempotent على reference (مرجع بوابة الدفع) — نفس reference بيرجع نفس
	النتيجة القديمة من غير ما يكرر الشحن.
	"""
	if PAYMENT_INTEGRATION_ROLE not in frappe.get_roles():
		frappe.throw(_("غير مصرح لك بعمل هذه العملية"), frappe.PermissionError)

	if not reference:
		frappe.throw(_("reference مطلوب لضمان عدم تكرار عملية الشحن"))

	amount = flt(amount)
	if amount <= 0:
		frappe.throw(_("المبلغ يجب أن يكون أكبر من صفر"))

	existing = frappe.db.get_value(
		"Wallet Transaction",
		{"reference": reference, "source": "mypay_topup"},
		["name", "balance_after"],
		as_dict=True,
	)
	if existing:
		return {"name": existing.name, "wallet": erp_customer_id, "balance": existing.balance_after, "created": False}

	if not frappe.db.exists("Wallet", erp_customer_id):
		frappe.throw(_("Wallet غير موجودة لهذا العميل"), frappe.DoesNotExistError)

	wt = frappe.new_doc("Wallet Transaction")
	wt.wallet = erp_customer_id
	wt.customer = erp_customer_id
	wt.type = "credit"
	wt.amount = amount
	wt.source = "mypay_topup"
	wt.reference = reference
	wt.status = "Completed"
	wt.insert(ignore_permissions=True)

	return {"name": wt.name, "wallet": erp_customer_id, "balance": wt.balance_after, "created": True}


@frappe.whitelist()
def manual_adjustment(customer, type, amount, reference):
	"""
	إيداع أو خصم يدوي من داخل ERPNext مباشرة (System Manager / Sales Manager فقط)
	POST /api/method/loyalpet.api.wallet.manual_adjustment
	"""
	if not set(frappe.get_roles()) & set(MANUAL_ADJUSTMENT_ROLES):
		frappe.throw(_("غير مصرح لك بعمل هذه العملية"), frappe.PermissionError)

	if type not in ("credit", "debit"):
		frappe.throw(_("النوع يجب أن يكون credit أو debit"))

	amount = flt(amount)
	if amount <= 0:
		frappe.throw(_("المبلغ يجب أن يكون أكبر من صفر"))

	if not reference:
		frappe.throw(_("لازم توضح سبب العملية"))

	if not frappe.db.exists("Wallet", customer):
		frappe.throw(_("Wallet غير موجودة لهذا العميل"), frappe.DoesNotExistError)

	wt = frappe.new_doc("Wallet Transaction")
	wt.wallet = customer
	wt.customer = customer
	wt.type = type
	wt.amount = amount
	wt.source = "admin_adjustment"
	wt.reference = reference
	wt.status = "Completed"
	wt.insert(ignore_permissions=True)

	return {"name": wt.name, "balance": wt.balance_after}


@frappe.whitelist()
def get_wallet_balance(erp_customer_id):
	"""
	إرجاع رصيد محفظة عميل معيّن
	POST /api/method/loyalpet.api.wallet.get_wallet_balance
	"""
	if PAYMENT_INTEGRATION_ROLE not in frappe.get_roles():
		frappe.throw(_("غير مصرح لك بعمل هذه العملية"), frappe.PermissionError)

	wallet = frappe.db.get_value(
		"Wallet", erp_customer_id, ["balance", "currency", "is_frozen"], as_dict=True
	)
	if not wallet:
		frappe.throw(_("Wallet غير موجودة لهذا العميل"), frappe.DoesNotExistError)

	return {
		"wallet": erp_customer_id,
		"balance": wallet.balance,
		"currency": wallet.currency,
		"is_frozen": wallet.is_frozen,
	}


@frappe.whitelist()
def get_wallet_transactions(erp_customer_id, limit=50):
	"""
	إرجاع آخر حركات محفظة عميل معيّن (الأحدث أولًا)
	POST /api/method/loyalpet.api.wallet.get_wallet_transactions
	"""
	if PAYMENT_INTEGRATION_ROLE not in frappe.get_roles():
		frappe.throw(_("غير مصرح لك بعمل هذه العملية"), frappe.PermissionError)

	if not frappe.db.exists("Wallet", erp_customer_id):
		frappe.throw(_("Wallet غير موجودة لهذا العميل"), frappe.DoesNotExistError)

	return frappe.get_all(
		"Wallet Transaction",
		filters={"wallet": erp_customer_id},
		fields=[
			"name", "type", "amount", "balance_before", "balance_after",
			"source", "reference", "status", "creation",
		],
		order_by="creation desc",
		limit_page_length=int(limit),
	)
