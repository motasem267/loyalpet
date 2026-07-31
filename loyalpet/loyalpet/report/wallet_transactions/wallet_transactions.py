import frappe
from frappe.utils import getdate, nowdate


def execute(filters=None):
	filters = filters or {}

	columns = [
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 180},
		{"label": "Date", "fieldname": "creation", "fieldtype": "Datetime", "width": 160},
		{"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 80},
		{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
		{"label": "Balance After", "fieldname": "balance_after", "fieldtype": "Currency", "width": 130},
		{"label": "Source", "fieldname": "source", "fieldtype": "Data", "width": 130},
		{"label": "Reference", "fieldname": "reference", "fieldtype": "Data", "width": 150},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
	]

	conditions = []
	values = {}

	if filters.get("customer"):
		conditions.append("wt.customer = %(customer)s")
		values["customer"] = filters["customer"]

	if filters.get("type"):
		conditions.append("wt.type = %(type)s")
		values["type"] = filters["type"]

	if filters.get("from_date"):
		conditions.append("DATE(wt.creation) >= %(from_date)s")
		values["from_date"] = getdate(filters["from_date"])

	if filters.get("to_date"):
		conditions.append("DATE(wt.creation) <= %(to_date)s")
		values["to_date"] = getdate(filters["to_date"])

	where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

	data = frappe.db.sql(f"""
		SELECT
			wt.customer,
			wt.creation,
			wt.type,
			wt.amount,
			wt.balance_after,
			wt.source,
			wt.reference,
			wt.status,
			w.customer AS wallet_customer
		FROM `tabWallet Transaction` wt
		LEFT JOIN `tabWallet` w ON w.name = wt.wallet
		{where}
		ORDER BY wt.creation DESC
		LIMIT 500
	""", values, as_dict=True)

	# Fallback: if customer not set on old records, use wallet's customer
	for row in data:
		if not row.customer and row.wallet_customer:
			row.customer = row.wallet_customer
		row.pop("wallet_customer", None)

	return columns, data
