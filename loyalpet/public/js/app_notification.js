const LOCKED_AFTER_SEND_FIELDS = ["send_to", "customers"];

frappe.ui.form.on("App Notification", {
	refresh(frm) {
		const already_sent = frm.doc.status && frm.doc.status !== "مسودة";

		// بعد الإرسال: مين استلم يفضل مقفول، لكن المحتوى (العنوان/النص/
		// الصورة/الإجراء) يفضل قابل للتعديل ويتبعت تحديثه للارافيل تلقائي
		LOCKED_AFTER_SEND_FIELDS.forEach((f) => frm.set_df_property(f, "read_only", already_sent ? 1 : 0));

		if (frm.is_new() || already_sent) return;

		frm.add_custom_button(__("إرسال"), () => {
			frappe.confirm(
				__("هل تريد إرسال الإشعار؟ لن يمكن إرساله مرة أخرى بعد ذلك."),
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
