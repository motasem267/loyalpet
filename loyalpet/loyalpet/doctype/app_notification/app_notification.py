import frappe
from frappe import _
from frappe.model.document import Document

DRAFT_STATUS = "مسودة"

# بعد الإرسال، دول وحدهم اللي يفضلوا مقفولين (مين استلم ومتى، والحالة نفسها) —
# المحتوى (العنوان/النص/الصورة/الإجراء) يفضل قابل للتعديل، والتعديل بيتبعت
# للارافيل عن طريق loyalpet.events.app_notification
LOCKED_AFTER_SEND = ("send_to", "status", "sent_at", "success_count", "failed_count", "result_detail")


class AppNotification(Document):
	def validate(self):
		if self.is_new():
			return

		before = self.get_doc_before_save()
		if not before or before.status == DRAFT_STATUS or self.flags.get("via_send_api"):
			return

		for fieldname in LOCKED_AFTER_SEND:
			if self.get(fieldname) != before.get(fieldname):
				frappe.throw(_("مينفعش تغيّر {0} بعد الإرسال").format(self.meta.get_label(fieldname)))

		before_customers = [r.customer for r in before.customers]
		after_customers = [r.customer for r in self.customers]
		if before_customers != after_customers:
			frappe.throw(_("مينفعش تغيّر قائمة الزبائن المستلمين بعد الإرسال"))
