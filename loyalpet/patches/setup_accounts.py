"""
Bind Chart of Accounts to company defaults, item groups, and payment modes.
"""
import frappe


def execute():
	company = frappe.db.get_value("Company", {"abbr": "LP"}, "name")
	if not company:
		frappe.log_error("setup_accounts patch: no company with abbr LP found")
		return

	_setup_company_defaults(company)
	_setup_item_group_accounts(company)
	_setup_payment_modes(company)
	frappe.db.commit()


def _setup_company_defaults(company):
	doc = frappe.get_doc("Company", company)
	doc.update({
		"default_receivable_account": "Debtors - LP",
		"default_payable_account": "Creditors - LP",
		"default_cash_account": "Cash - LP",
		"round_off_account": "Round Off - LP",
		"write_off_account": "Write Off - LP",
		"exchange_gain_loss_account": "Exchange Gain/Loss - LP",
		"default_income_account": "Sales - LP",
	})
	doc.save(ignore_permissions=True)


def _set_item_group_accounts(group_name, company, income_account, expense_account):
	if not frappe.db.exists("Item Group", group_name):
		return
	doc = frappe.get_doc("Item Group", group_name)
	# item_group_defaults is a Table of "Item Default" child docs
	existing = next(
		(r for r in doc.item_group_defaults if r.company == company), None
	)
	if existing:
		existing.income_account = income_account
		existing.expense_account = expense_account
	else:
		doc.append("item_group_defaults", {
			"company": company,
			"income_account": income_account,
			"expense_account": expense_account,
		})
	doc.save(ignore_permissions=True)


def _setup_item_group_accounts(company):
	# ── منتجات (قطط / كلاب / أسماك وكل مجموعاتهم الفرعية) ──────────────────
	product_groups = [
		"قطط", "طعام قطط", "مستلزمات قطط", "Royal Elite",
		"كلاب", "طعام كلاب", "مستلزمات كلاب",
		"أسماك", "طعام أسماك", "مستلزمات أسماك",
	]
	for g in product_groups:
		_set_item_group_accounts(g, company, "Sales - LP", "Cost of Goods Sold - LP")

	# ── خدمات بيطرية ─────────────────────────────────────────────────────────
	_set_item_group_accounts(
		"بيطرة", company,
		"Veterinary - LP",
		"Veterinary Supplies Cost - LP",
	)

	# ── فندقة / إيواء ────────────────────────────────────────────────────────
	_set_item_group_accounts(
		"فندقة (إيواء)", company,
		"Host - LP",
		"Boarding Supplies Cost - LP",
	)

	# ── مجموعة الخدمات الأم ──────────────────────────────────────────────────
	_set_item_group_accounts("خدمات", company, "Sales - LP", "Services Expenses - LP")


def _setup_payment_mode(name, mode_type, account, company):
	if not frappe.db.exists("Mode of Payment", name):
		frappe.get_doc({
			"doctype": "Mode of Payment",
			"mode_of_payment": name,
			"type": mode_type,
		}).insert(ignore_permissions=True)

	doc = frappe.get_doc("Mode of Payment", name)
	existing = next((a for a in doc.accounts if a.company == company), None)
	if existing:
		existing.default_account = account
	else:
		doc.append("accounts", {"company": company, "default_account": account})
	doc.save(ignore_permissions=True)


def _setup_payment_modes(company):
	_setup_payment_mode("Cash", "Cash", "Cash - LP", company)
	_setup_payment_mode("E-Wallet", "Bank", "E-Wallet - LP", company)
	_setup_payment_mode("Wire Transfer", "Bank", "Bank - LP", company)
	_setup_payment_mode("Cheque", "Bank", "Bank - LP", company)
	_setup_payment_mode("Bank Draft", "Bank", "Bank - LP", company)
	_setup_payment_mode("Credit Card", "Bank", "Bank - LP", company)
