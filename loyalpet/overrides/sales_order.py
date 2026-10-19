import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from erpnext.accounts.party import get_party_account
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder

from loyalpet.api.orders import BANK_TRANSFER, STATE_AWAITING_TRANSFER, STATE_UNDER_REVIEW

TRANSFER_MODE_OF_PAYMENT = "حوالة"


class CustomSalesOrder(SalesOrder):
	def validate(self):
		# ERPNext 15 bug: taxes child table is None when doc is built from JSON without taxes field
		if self.get("taxes") is None:
			self.set("taxes", [])

		super().validate()

	def on_update(self):
		super().on_update()
		if self._is_transfer_confirmation():
			self._create_transfer_payment_entry()

	def _is_transfer_confirmation(self):
		"""الموظف طابق الإيصال ونقل الطلب "بانتظار تأكيد الحوالة" -> "قيد المراجعة"
		(عن طريق الـ Workflow). تنقّل الزبون بين الحالتين ما يمرش من هني، لأنه
		بيحصل مباشرة على الداتابيز (loyalpet.api.orders._set_state)."""
		before = self.get_doc_before_save()
		return (
			before
			and before.custom_workflow_state == STATE_AWAITING_TRANSFER
			and self.custom_workflow_state == STATE_UNDER_REVIEW
			and self.custom_payment_method == BANK_TRANSFER
			and not self.custom_transfer_payment_entry
		)

	def _create_transfer_payment_entry(self):
		"""الطلب لسه Draft فما ينفعش يتربط بالـ Payment Entry، فالفلوس تتسجل
		كدفعة مقدمة (Advance) على الزبون، وتتخصم من الفاتورة وقت الفوترة
		(loyalpet.events.sales_invoice.before_validate)."""
		today = frappe.utils.today()
		amount = self.rounded_total or self.grand_total

		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Receive"
		pe.company = self.company
		pe.posting_date = today
		pe.mode_of_payment = TRANSFER_MODE_OF_PAYMENT
		pe.party_type = "Customer"
		pe.party = self.customer
		pe.paid_from = get_party_account("Customer", self.customer, self.company)
		pe.paid_to = get_bank_cash_account(TRANSFER_MODE_OF_PAYMENT, self.company)["account"]
		pe.paid_amount = amount
		pe.received_amount = amount
		pe.reference_no = self.name
		pe.reference_date = today
		pe.remarks = f"حوالة مصرفية للطلب {self.name}"
		pe.flags.ignore_permissions = True
		pe.insert()
		pe.submit()

		self.db_set("custom_transfer_payment_entry", pe.name, update_modified=False)
