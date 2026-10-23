import frappe

DRAFT_STATUS = "مسودة"


def _build_action(doc):
	if doc.action_type == "منتج معين":
		return {"type": "item", "item_code": doc.action_item}
	elif doc.action_type == "تصنيف":
		return {"type": "item_group", "item_group": doc.action_item_group}
	elif doc.action_type == "رابط":
		return {"type": "url", "url": doc.action_url}
	return {"type": "none"}


def _send(payload):
	secret = frappe.conf.get("loyalpet_webhook_secret")
	url = frappe.conf.get("loyalpet_backend_url")
	if not secret or not url:
		frappe.log_error(
			"loyalpet_webhook_secret/loyalpet_backend_url missing in site_config",
			"LoyalPet App Notification Sync",
		)
		return
	frappe.enqueue(
		"loyalpet.events.webhook_utils._send_signed_payload",
		queue="default",
		url=url,
		secret=secret,
		payload=payload,
	)


def notify_content_update(doc, method):
	"""لو الإشعار اتبعت بالفعل وحد عدّل محتواه بعد كده (مش أول إرسال)، نبلّغ
	لارافيل بالتعديل عشان يحدّث اللي ظاهر للعميل. أول إرسال نفسه (عن طريق
	send_app_notification) بيبلّغ لوحده، مش محتاج تكرار هنا."""
	if doc.status == DRAFT_STATUS or doc.flags.get("via_send_api"):
		return

	_send({
		"doctype": "App Notification",
		"event": "updated",
		"name": doc.name,
		"title": doc.title,
		"body": doc.body,
		"image": doc.image,
		"action": _build_action(doc),
	})


def notify_deleted(doc, method):
	if doc.status == DRAFT_STATUS:
		return  # لسه مسودة، لارافيل أصلاً معندوش حاجة يمسحها
	_send({"doctype": "App Notification", "event": "deleted", "name": doc.name})
