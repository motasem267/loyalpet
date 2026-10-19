frappe.listview_settings["Sales Order"] = frappe.listview_settings["Sales Order"] || {};

const erpnext_sales_order_onload = frappe.listview_settings["Sales Order"].onload;

Object.assign(frappe.listview_settings["Sales Order"], {
	onload(listview) {
		if (erpnext_sales_order_onload) {
			erpnext_sales_order_onload(listview);
		}

		// الحوالات اللي تستنى الموظف يطابق إيصالها مع كشف الحساب
		listview.page.add_inner_button(__("حوالات بانتظار التأكيد"), () => {
			listview.filter_area.clear(false).then(() => {
				listview.filter_area.add([
					["Sales Order", "custom_workflow_state", "=", "بانتظار تأكيد الحوالة"],
				]);
			});
		});
	},
});
