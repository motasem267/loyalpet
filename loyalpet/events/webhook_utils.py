import base64
import hashlib
import hmac
import json

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


def send_rename_notification(doctype, old_name, new_name):
	"""إشعار مخصص وقت rename — الاسم القديم مش حقل حقيقي على المستند، فمفيش
	طريقة نوصّله عن طريق webhook_data العادي (بيعتمد على doc.as_dict()، وده
	بيرجع بس الحقول المعرّفة فعليًا). بنبني ونوقّع ونبعت الـ payload يدويًا،
	بنفس السيكرت والرابط المستخدمين في باقي الويب هوكس، عشان لارافيل يقدر
	يعمل rename حقيقي (يبدّل الاسم ويكاسكيد على المنتجات/الفروع) بدل ما
	يضيف سجل جديد."""
	secret = frappe.conf.get("loyalpet_webhook_secret")
	url = frappe.conf.get("loyalpet_backend_url")
	if not secret or not url:
		frappe.log_error(
			"loyalpet_webhook_secret/loyalpet_backend_url missing in site_config",
			"LoyalPet Rename Notification",
		)
		return

	payload = {
		"doctype": doctype,
		"event": "renamed",
		"old_name": old_name,
		"new_name": new_name,
	}
	frappe.enqueue(
		"loyalpet.events.webhook_utils._send_signed_payload",
		queue="default",
		url=url,
		secret=secret,
		payload=payload,
	)


def _send_signed_payload(url, secret, payload):
	import requests

	body = json.dumps(payload).encode("utf8")
	signature = base64.b64encode(
		hmac.new(secret.encode("utf8"), body, hashlib.sha256).digest()
	).decode()
	try:
		response = requests.post(
			url,
			data=body,
			headers={"Content-Type": "application/json", "X-Frappe-Webhook-Signature": signature},
			timeout=10,
		)
		response.raise_for_status()
	except Exception:
		frappe.log_error(
			f"url: {url}\npayload: {payload}\nresponse: {getattr(locals().get('response'), 'text', None)}\n\n{frappe.get_traceback()}",
			"LoyalPet Rename Notification Failed",
		)
		raise
