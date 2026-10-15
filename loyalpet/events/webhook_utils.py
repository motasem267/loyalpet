import frappe


def notify_webhook(doc, webhook_name):
	"""بتفعّل ويب هوك معيّن يدويًا — للحالات اللي بتغيّر المستند من غير ما تمر
	بـ doc.save() العادي (زي rename_doc، أو تحديث مباشر على الداتابيز)،
	واللي الويب هوكس العادية (on_update/after_insert) مابتتفعلش معاها تلقائي."""
	wh = frappe.db.get_value("Webhook", {"name": webhook_name, "enabled": 1}, "name")
	if wh:
		frappe.enqueue(
			"frappe.integrations.doctype.webhook.webhook.enqueue_webhook",
			doc=doc,
			webhook={"name": wh},
			queue="default",
		)
