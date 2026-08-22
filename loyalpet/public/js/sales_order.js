frappe.ui.form.on("Sales Order", {
	refresh(frm) {
		// Always remove the default ERPNext "Create > Sales Invoice" button
		frm.remove_custom_button(__("Sales Invoice"), __("Create"));

		if (frm.doc.custom_workflow_state === "تم الاستلام" && frappe.model.can_create("Sales Invoice")) {
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
		}

		// طلب لسه "قيد المراجعة" (Draft) — محرك الـ Workflow مايسمحش بانتقال
		// Draft->Cancelled عادي، فبنعرض زرار مباشر بيستخدم reject_sales_order
		if (frm.doc.custom_workflow_state === "قيد المراجعة" && frm.doc.docstatus === 0) {
			frm.add_custom_button(__("رفض الطلب"), () => {
				frappe.confirm(__("متأكد إنك عايز ترفض/تلغي الطلب ده؟"), () => {
					frappe.call({
						method: "loyalpet.api.orders.reject_sales_order",
						args: { name: frm.doc.name },
						freeze: true,
						freeze_message: __("جاري الإلغاء..."),
						callback(r) {
							if (r.message) {
								frappe.show_alert({ message: __("تم إلغاء الطلب"), indicator: "red" });
								frm.reload_doc();
							}
						},
					});
				});
			}).addClass("btn-danger");
		}
	},
});
