frappe.ui.form.on("Wallet", {
	refresh(frm) {
		if (frm.is_new()) return;
		if (!frappe.user_roles.includes("System Manager") && !frappe.user_roles.includes("Sales Manager")) return;

		frm.add_custom_button(__("إيداع / خصم يدوي"), () => {
			const dialog = new frappe.ui.Dialog({
				title: __("عملية يدوية على المحفظة"),
				fields: [
					{
						fieldname: "type",
						label: __("نوع العملية"),
						fieldtype: "Select",
						options: [
							{ label: __("إيداع"), value: "credit" },
							{ label: __("خصم"), value: "debit" },
						],
						reqd: 1,
					},
					{ fieldname: "amount", label: __("المبلغ"), fieldtype: "Currency", reqd: 1 },
					{ fieldname: "reference", label: __("سبب العملية"), fieldtype: "Data", reqd: 1 },
				],
				primary_action_label: __("تنفيذ"),
				primary_action(values) {
					frappe.call({
						method: "loyalpet.api.wallet.manual_adjustment",
						args: {
							customer: frm.doc.customer,
							type: values.type,
							amount: values.amount,
							reference: values.reference,
						},
						freeze: true,
						freeze_message: __("جاري التنفيذ..."),
						callback(r) {
							if (r.message) {
								dialog.hide();
								frappe.show_alert({
									message: __("تم بنجاح. الرصيد الجديد: {0}", [r.message.balance]),
									indicator: "green",
								});
								frm.reload_doc();
							}
						},
					});
				},
			});
			dialog.show();
		});
	},
});
