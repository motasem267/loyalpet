"""
إنشاء الـ Webhooks الخاصة بمزامنة loyalpet مع Laravel (idempotent).

ليه patch مش fixture: webhook_secret حقل Password، وأي fixture ليه بيتصدّر
مقنّع (***) وده بيفشّل bench migrate (Invalid Webhook Secret) لما يحاول
يستورده. فبدل كده السيكرت والرابط بييجوا من site_config.json، أبدًا مش من git.

قبل ما الباتش يعمل حاجة، لازم تظبط الإعدادين دول على البيئة الحالية:
	bench --site <site> set-config loyalpet_webhook_secret "<نفس القيمة اللي عند Laravel>"
	bench --site <site> set-config loyalpet_laravel_url "https://api.loyalpet.ly"

الباتش بيتخطى أي Webhook موجود بالفعل بنفس الاسم (منفّذ من غير ما يلمس
السيكرت الحالي لو كان مظبوط يدويًا قبل كده).
"""
import frappe

WEBHOOK_URL_PATH = "/api/v1/webhooks/erp"

WEBHOOKS = [
	{
		"name": "LoyalPet Customer Sync (Create)",
		"webhook_doctype": "Customer",
		"webhook_docevent": "after_insert",
		"webhook_data": [
			("doctype", "doctype"), ("name", "erp_customer_id"), ("customer_name", "name"),
			("custom_phone", "phone"), ("custom_address", "address"),
			("custom_app_user_id", "custom_app_user_id"),
		],
	},
	{
		"name": "LoyalPet Customer Sync (Update)",
		"webhook_doctype": "Customer",
		"webhook_docevent": "on_update",
		"webhook_data": [
			("doctype", "doctype"), ("name", "name"), ("customer_name", "customer_name"),
			("custom_app_user_id", "custom_app_user_id"),
		],
	},
	{
		"name": "LoyalPet Sales Order Sync",
		"webhook_doctype": "Sales Order",
		"webhook_docevent": "on_update",
		"condition": 'doc.has_value_changed("custom_workflow_state")',
		"webhook_data": [
			("doctype", "doctype"), ("name", "name"), ("customer", "customer"),
			("grand_total", "grand_total"), ("custom_workflow_state", "custom_workflow_state"),
			("custom_payment_method", "custom_payment_method"),
		],
	},
	{
		"name": "LoyalPet Item Sync",
		"webhook_doctype": "Item",
		"webhook_docevent": "on_update",
		"webhook_data": [
			("doctype", "doctype"), ("name", "name"), ("item_code", "item_code"),
			("item_name", "item_name"), ("item_group", "item_group"),
			("description", "description"), ("image", "image"),
			("standard_rate", "standard_rate"), ("disabled", "disabled"),
		],
	},
	{
		"name": "LoyalPet Item Sync (Create)",
		"webhook_doctype": "Item",
		"webhook_docevent": "after_insert",
		"webhook_data": [
			("doctype", "doctype"), ("name", "name"), ("item_code", "item_code"),
			("item_name", "item_name"), ("item_group", "item_group"),
			("description", "description"), ("image", "image"),
			("standard_rate", "standard_rate"), ("disabled", "disabled"),
		],
	},
	{
		"name": "LoyalPet Item Group Sync",
		"webhook_doctype": "Item Group",
		"webhook_docevent": "on_update",
		"webhook_data": [
			("doctype", "doctype"), ("name", "name"),
			("parent_item_group", "parent_item_group"), ("is_group", "is_group"),
			("image", "image"),
		],
	},
	{
		"name": "LoyalPet Item Group Sync (Create)",
		"webhook_doctype": "Item Group",
		"webhook_docevent": "after_insert",
		"webhook_data": [
			("doctype", "doctype"), ("name", "name"),
			("parent_item_group", "parent_item_group"), ("is_group", "is_group"),
			("image", "image"),
		],
	},
	{
		"name": "LoyalPet Product Bundle Sync",
		"webhook_doctype": "Product Bundle",
		"webhook_docevent": "on_update",
		"webhook_data": [
			("doctype", "doctype"), ("name", "name"), ("new_item_code", "new_item_code"),
			("description", "description"), ("custom_image", "custom_image"),
		],
	},
	{
		"name": "LoyalPet Product Bundle Sync (Create)",
		"webhook_doctype": "Product Bundle",
		"webhook_docevent": "after_insert",
		"webhook_data": [
			("doctype", "doctype"), ("name", "name"), ("new_item_code", "new_item_code"),
			("description", "description"), ("custom_image", "custom_image"),
		],
	},
	{
		"name": "LoyalPet Wallet Transaction Sync",
		"webhook_doctype": "Wallet Transaction",
		"webhook_docevent": "after_insert",
		"webhook_data": [
			("doctype", "doctype"), ("name", "name"), ("wallet", "wallet"),
			("customer", "customer"), ("type", "type"), ("amount", "amount"),
			("balance_after", "balance_after"), ("source", "source"), ("reference", "reference"),
		],
	},
	{
		"name": "LoyalPet Vet Appointment Sync (Create)",
		"webhook_doctype": "Vet Appointment",
		"webhook_docevent": "after_insert",
		"webhook_data": [
			("doctype", "doctype"), ("name", "name"), ("customer", "customer"),
			("status", "status"), ("appointment_date", "appointment_date"),
			("appointment_time", "appointment_time"),
		],
	},
	{
		"name": "LoyalPet Vet Appointment Sync (Update)",
		"webhook_doctype": "Vet Appointment",
		"webhook_docevent": "on_update",
		"webhook_data": [
			("doctype", "doctype"), ("name", "name"), ("customer", "customer"),
			("status", "status"), ("appointment_date", "appointment_date"),
			("appointment_time", "appointment_time"),
		],
	},
	{
		"name": "LoyalPet Hotel Booking Sync (Create)",
		"webhook_doctype": "Hotel Booking",
		"webhook_docevent": "after_insert",
		"webhook_data": [
			("doctype", "doctype"), ("name", "name"), ("customer", "customer"), ("status", "status"),
		],
	},
	{
		"name": "LoyalPet Hotel Booking Sync (Update)",
		"webhook_doctype": "Hotel Booking",
		"webhook_docevent": "on_update",
		"webhook_data": [
			("doctype", "doctype"), ("name", "name"), ("customer", "customer"), ("status", "status"),
		],
	},
]


def execute():
	secret = frappe.conf.get("loyalpet_webhook_secret")
	base_url = frappe.conf.get("loyalpet_laravel_url")

	if not secret or not base_url:
		frappe.logger().warning(
			"loyalpet: skipping webhook setup - set 'loyalpet_webhook_secret' and "
			"'loyalpet_laravel_url' in site_config.json (bench set-config), then "
			"re-run: bench execute loyalpet.patches.setup_webhooks.execute"
		)
		return

	request_url = base_url.rstrip("/") + WEBHOOK_URL_PATH

	for wh in WEBHOOKS:
		if frappe.db.exists("Webhook", wh["name"]):
			continue

		doc = frappe.new_doc("Webhook")
		doc.name = wh["name"]
		doc.webhook_doctype = wh["webhook_doctype"]
		doc.webhook_docevent = wh["webhook_docevent"]
		doc.condition = wh.get("condition")
		doc.request_url = request_url
		doc.request_method = "POST"
		doc.webhook_secret = secret
		doc.timeout = 15
		doc.enabled = 1
		for fieldname, key in wh["webhook_data"]:
			doc.append("webhook_data", {"fieldname": fieldname, "key": key})
		doc.insert(ignore_permissions=True)

	frappe.db.commit()
