import frappe
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder


class CustomSalesOrder(SalesOrder):
	def validate(self):
		# ERPNext 15 bug: taxes child table is None when doc is built from JSON without taxes field
		if self.get("taxes") is None:
			self.set("taxes", [])

		super().validate()
