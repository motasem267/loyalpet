import frappe


@frappe.whitelist()
def get_delivery_zones():
	"""
	كل مناطق التوصيل النشطة مع أسعارها
	POST /api/method/loyalpet.api.delivery_zones.get_delivery_zones
	"""
	return frappe.get_all(
		"Delivery Zone",
		filters={"is_active": 1},
		fields=["name", "zone_name", "delivery_price"],
		order_by="zone_name asc",
	)
