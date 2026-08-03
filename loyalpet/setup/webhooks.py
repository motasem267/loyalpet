import frappe


def configure_webhooks():
    """Apply per-site webhook secret + backend URL after migrate."""
    secret = frappe.conf.get("loyalpet_webhook_secret")
    url = frappe.conf.get("loyalpet_backend_url")

    if not secret:
        frappe.log_error("loyalpet_webhook_secret missing in site_config", "LoyalPet Webhooks")
        return

    for name in frappe.get_all("Webhook", filters={"name": ["like", "LoyalPet%"]}, pluck="name"):
        doc = frappe.get_doc("Webhook", name)
        if url:
            doc.request_url = url
        doc.enable_security = 1
        doc.webhook_secret = secret
        doc.save(ignore_permissions=True)

    frappe.db.commit()
