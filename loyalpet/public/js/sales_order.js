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

		// طلب لسه "قيد المراجعة" أو "بانتظار تأكيد الحوالة" (Draft) — محرك الـ Workflow
		// مايسمحش بانتقال Draft->Cancelled عادي، فبنعرض زرار مباشر بيستخدم reject_sales_order
		const awaiting_transfer = frm.doc.custom_workflow_state === "بانتظار تأكيد الحوالة";
		if ((frm.doc.custom_workflow_state === "قيد المراجعة" || awaiting_transfer) && frm.doc.docstatus === 0) {
			frm.add_custom_button(__("رفض الطلب"), () => {
				frappe.prompt(
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: __("سبب الرفض (يظهر للزبون)"),
						reqd: awaiting_transfer ? 1 : 0,
					},
					({ reason }) => {
						frappe.call({
							method: "loyalpet.api.orders.reject_sales_order",
							args: { name: frm.doc.name, reason },
							freeze: true,
							freeze_message: __("جاري الإلغاء..."),
							callback(r) {
								if (r.message) {
									frappe.show_alert({ message: __("تم إلغاء الطلب"), indicator: "red" });
									frm.reload_doc();
								}
							},
						});
					},
					frm.doc.custom_transfer_payment_entry
						? __("الحوالة متأكدة ومسجلة — لازم ترجيع الفلوس يدويًا بعد الرفض")
						: __("رفض الطلب"),
					__("رفض"),
				);
			}).addClass("btn-danger");
		}
	},
});
