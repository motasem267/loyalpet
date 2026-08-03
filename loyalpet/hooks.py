app_name = "loyalpet"
app_title = "LoyalPet"
app_publisher = "motasem"
app_description = "loyal pet "
app_email = "motasemsaklul2001@gmail.com"
app_license = "mit"

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [["name", "in", [
			"Sales Order-custom_workflow_state",
			"Sales Order-custom_from_app",
			"Sales Order-custom_app_reference",
			"Sales Order-custom_payment_method",
			"Sales Order-custom_rejection_reason",
			"Sales Order-custom_recipient_name",
			"Sales Order-custom_recipient_phone",
			"Sales Order-custom_delivery_address",
			"Sales Order-custom_notes",
			"Customer-custom_app_user_id",
			"Customer-custom_phone",
			"Customer-custom_address",
			"Item-custom_show_in_app",
			"Item-custom_is_featured",
			"Item-custom_featured_order",
			"Employee-custom_employee_type",
			"Product Bundle-custom_image",
		]]],
	},
	{
		"dt": "Workflow State",
		"filters": [["name", "in", [
			"قيد المراجعة", "قيد التوصيل", "خطأ في عملية الدفع",
			"مكتملة", "تم الاستلام", "تعذر الاستلام", "ملغي",
		]]],
	},
	{
		"dt": "Workflow Action Master",
		"filters": [["name", "in", [
			"موافقة", "رفض", "تسليم", "تعذر التسليم", "إلغاء", "إعادة محاولة",
		]]],
	},
	{
		"dt": "Workflow",
		"filters": [["name", "=", "Sales Order Workflow"]],
	},
	{
		"dt": "Number Card",
		"filters": [["name", "in", [
			"Active Wallets", "Total Wallet Balance", "Available Vouchers",
			"Today Vet Appointments", "Total Vet Appointments", "Vet Service Types Count",
			"Total Active Rooms", "Active Hotel Bookings", "Today Hotel Bookings",
			"Available Rooms Today",
		]]],
	},
	{
		"dt": "Workspace",
		"filters": [["name", "in", ["Wallets", "Vet", "Hotel"]]],
	},
	{
		"dt": "Role",
		"filters": [["name", "=", "Wallet Payment Integration"]],
	},
]

# ملاحظة: الـ Webhooks (بما فيهم webhook_secret) عمدًا مش fixtures — لأن
# webhook_secret حقل Password، بيتصدّر مقنّع (***) في أي fixture، وده يخلي
# `bench migrate` يفشل (Invalid Webhook Secret) لما يحاول يستوردها.
# بدل كده بيتظبطوا بعد كل migrate عبر after_migrate تحت، والسيكرت والرابط
# بيتجابوا من site_config.json (loyalpet_webhook_secret / loyalpet_backend_url).

after_migrate = ["loyalpet.setup.webhooks.configure_webhooks"]

override_doctype_class = {
	"Sales Order": "loyalpet.overrides.sales_order.CustomSalesOrder",
}

doc_events = {
	"Customer": {
		"after_insert": "loyalpet.events.customer.on_customer_created",
	},
	"Sales Invoice": {
		"validate": "loyalpet.events.sales_invoice.validate",
		"on_submit": "loyalpet.events.sales_invoice.on_submit",
	},
	"Wallet Transaction": {
		"validate": "loyalpet.events.wallet.validate",
		"on_trash": "loyalpet.events.wallet.on_trash",
	},
	"Item Price": {
		"after_insert": "loyalpet.events.item_price.sync_standard_rate",
		"on_update": "loyalpet.events.item_price.sync_standard_rate",
	},
}

scheduler_events = {
	"daily": [
		"loyalpet.tasks.send_appointment_reminders",
		"loyalpet.tasks.expire_vouchers",
	],
	"hourly": [
		"loyalpet.tasks.check_hotel_checkouts",
	],
}

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "loyalpet",
# 		"logo": "/assets/loyalpet/logo.png",
# 		"title": "LoyalPet",
# 		"route": "/loyalpet",
# 		"has_permission": "loyalpet.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/loyalpet/css/workspace.css"
app_include_js = "/assets/loyalpet/js/workspace.js"

# include js in doctype views
doctype_js = {
	"Sales Order": "public/js/sales_order.js",
	"Wallet": "public/js/wallet.js",
}

# include js, css files in header of web template
# web_include_css = "/assets/loyalpet/css/loyalpet.css"
# web_include_js = "/assets/loyalpet/js/loyalpet.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "loyalpet/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "loyalpet/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "loyalpet.utils.jinja_methods",
# 	"filters": "loyalpet.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "loyalpet.install.before_install"
# after_install = "loyalpet.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "loyalpet.uninstall.before_uninstall"
# after_uninstall = "loyalpet.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "loyalpet.utils.before_app_install"
# after_app_install = "loyalpet.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "loyalpet.utils.before_app_uninstall"
# after_app_uninstall = "loyalpet.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "loyalpet.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"loyalpet.tasks.all"
# 	],
# 	"daily": [
# 		"loyalpet.tasks.daily"
# 	],
# 	"hourly": [
# 		"loyalpet.tasks.hourly"
# 	],
# 	"weekly": [
# 		"loyalpet.tasks.weekly"
# 	],
# 	"monthly": [
# 		"loyalpet.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "loyalpet.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "loyalpet.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "loyalpet.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["loyalpet.utils.before_request"]
# after_request = ["loyalpet.utils.after_request"]

# Job Events
# ----------
# before_job = ["loyalpet.utils.before_job"]
# after_job = ["loyalpet.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"loyalpet.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

