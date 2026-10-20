frappe.ui.form.on("App Notification", {
	refresh(frm) {
		if (frm.doc.status && frm.doc.status !== "مسودة") {
			frm.disable_form();
			return;
		}

		if (frm.is_new()) return;

		frm.add_custom_button(__("إرسال"), () => {
			frappe.confirm(
				__("هل تريد إرسال الإشعار؟ لا يمكن تعديله بعد الإرسال."),
				() => {
					frappe.call({
						method: "loyalpet.api.notifications.send_app_notification",
						args: { name: frm.doc.name },
						freeze: true,
						freeze_message: __("جاري الإرسال..."),
						callback(r) {
							frm.reload_doc();
							if (r.message) {
								const failed = r.message.status === "فشل";
								frappe.show_alert({
									message: failed
										? __("فشل الإرسال")
										: __("تم الإرسال — نجح: {0}، فشل: {1}", [
												r.message.success_count,
												r.message.failed_count,
										  ]),
									indicator: failed ? "red" : "green",
								});
							}
						},
					});
				}
			);
		}).addClass("btn-primary");
	},
});
