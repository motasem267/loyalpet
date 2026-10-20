import json

import frappe
from frappe import _

from loyalpet.events.webhook_utils import sign_payload

ALLOWED_ROLES = ("System Manager", "Sales Manager")
DRAFT_STATUS = "مسودة"
SENT_STATUS = "تم الإرسال"
FAILED_STATUS = "فشل"


def _check_permission():
	if not set(ALLOWED_ROLES) & set(frappe.get_roles()):
		frappe.throw(_("مالكش صلاحية ترسل إشعارات"), frappe.PermissionError)


def _build_payload(doc):
	payload = {
		"doctype": "App Notification",
		"title": doc.title,
		"body": doc.body,
		"image": doc.image,
		"send_to": "all" if doc.send_to == "كل المستخدمين" else "specific",
	}
	if doc.send_to == "زبائن محددين":
		payload["customer_ids"] = [row.customer for row in doc.customers]

	if doc.action_type == "منتج معين":
		action = {"type": "item", "item_code": doc.action_item}
	elif doc.action_type == "تصنيف":
		action = {"type": "item_group", "item_group": doc.action_item_group}
	elif doc.action_type == "رابط":
		action = {"type": "url", "url": doc.action_url}
	else:
		action = {"type": "none"}
	payload["action"] = action

	return payload


@frappe.whitelist()
def send_app_notification(name):
	_check_permission()

	doc = frappe.get_doc("App Notification", name)
	if doc.status != DRAFT_STATUS:
		frappe.throw(_("الإشعار ده اتبعت بالفعل، مينفعش يتبعت تاني"))

	if doc.send_to == "زبائن محددين" and not doc.customers:
		frappe.throw(_("اختار زبائن محددين الأول، أو غيّر الإرسال لـ'كل المستخدمين'"))

	secret = frappe.conf.get("loyalpet_webhook_secret")
	url = frappe.conf.get("loyalpet_backend_url")
	if not secret or not url:
		frappe.throw(_("إعدادات الربط مع لارافيل ناقصة في السيرفر (loyalpet_webhook_secret/loyalpet_backend_url)"))

	payload = _build_payload(doc)
	body = json.dumps(payload).encode("utf8")
	signature = sign_payload(secret, body)

	success_count, failed_count = 0, 0
	try:
		import requests

		response = requests.post(
			url,
			data=body,
			headers={"Content-Type": "application/json", "X-Frappe-Webhook-Signature": signature},
			timeout=20,
		)
		response.raise_for_status()
		resp_data = response.json()
		success_count = frappe.utils.cint(resp_data.get("success_count"))
		failed_count = frappe.utils.cint(resp_data.get("failed_count"))
		doc.status = SENT_STATUS
		doc.result_detail = response.text[:5000]
	except Exception:
		doc.status = FAILED_STATUS
		doc.result_detail = frappe.get_traceback()[:5000]
		frappe.log_error(
			f"payload: {payload}\n\n{frappe.get_traceback()}",
			"LoyalPet App Notification Send Failed",
		)

	doc.sent_at = frappe.utils.now_datetime()
	doc.success_count = success_count
	doc.failed_count = failed_count
	doc.flags.via_send_api = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {"status": doc.status, "success_count": doc.success_count, "failed_count": doc.failed_count}
