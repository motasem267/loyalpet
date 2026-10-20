import frappe
from frappe import _
from frappe.model.document import Document

DRAFT_STATUS = "مسودة"


class AppNotification(Document):
	def validate(self):
		if self.is_new():
			return

		before = self.get_doc_before_save()
		if before and before.status != DRAFT_STATUS and not self.flags.get("via_send_api"):
			frappe.throw(_("الإشعار ده اتبعت بالفعل، مينفعش يتعدل"))
