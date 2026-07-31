frappe.ui.form.on("Sales Order", {
	refresh(frm) {
		// Always remove the default ERPNext "Create > Sales Invoice" button
		frm.remove_custom_button(__("Sales Invoice"), __("Create"));

		if (frm.doc.custom_workflow_state !== "تم الاستلام") return;
		if (!frappe.model.can_create("Sales Invoice")) return;

		// Re-add it with direct open (no background notification)
		frm.add_custom_button(__("Sales Invoice"), () => {
			frappe.call({
				method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
				args: { source_name: frm.doc.name },
				freeze: true,
				freeze_message: __("Creating Sales Invoice..."),
				callback(r) {
					if (r.message) {
						frappe.model.sync(r.message);
						frappe.set_route("Form", "Sales Invoice", r.message.name);
					}
				},
			});
		}, __("Create"));
	},
});
