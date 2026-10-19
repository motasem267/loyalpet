"""
طرق الدفع "بطاقة" (ماكينة المندوب) و"حوالة" (المصرف الإسلامي الليبي)، كل وحدة
مربوطة بحساب بنكي خاص بيها، باش الحسابات تفرّق بين النقدي والبطاقة والحوالة.

الحسابات بتتعمل بس لو مش موجودة، وربط طريقة الدفع بالحساب ما يتلمسش لو حد
ظبطه يدويًا قبل — عشان ما نكسرش أي تعديل اتعمل على السيرفر.
"""
import frappe

from loyalpet.patches.setup_accounts import _setup_payment_mode

PAYMENT_MODES = [
	# (طريقة الدفع، اسم الحساب)
	("بطاقة", "ماكينة البطاقات"),
	("حوالة", "المصرف الإسلامي الليبي"),
]


def execute():
	company = frappe.db.get_value("Company", {"abbr": "LP"}, ["name", "abbr"], as_dict=True)
	if not company:
		frappe.log_error("setup_card_transfer_payment_modes patch: no company with abbr LP found")
		return

	for mode, account_name in PAYMENT_MODES:
		already_mapped = frappe.db.get_value(
			"Mode of Payment Account", {"parent": mode, "company": company.name}, "default_account"
		)
		if already_mapped:
			continue
		account = _ensure_bank_account(account_name, company)
		_setup_payment_mode(mode, "Bank", account, company.name)

	frappe.db.commit()


def _ensure_bank_account(account_name, company):
	name = f"{account_name} - {company.abbr}"
	if not frappe.db.exists("Account", name):
		frappe.get_doc({
			"doctype": "Account",
			"account_name": account_name,
			"parent_account": f"Bank Accounts - {company.abbr}",
			"company": company.name,
			"account_type": "Bank",
			"is_group": 0,
		}).insert(ignore_permissions=True)
	return name
