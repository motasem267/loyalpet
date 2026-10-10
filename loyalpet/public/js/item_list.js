frappe.listview_settings["Item"] = frappe.listview_settings["Item"] || {};

Object.assign(frappe.listview_settings["Item"], {
	onload(listview) {
		// منتجات بدون سعر بيع — نستثني التمبلت (has_variants) لأن سعره
		// طبيعي يكون فاضي، السعر الحقيقي موجود في كل variant لوحده.
		listview.page.add_inner_button(__("بدون سعر"), () => {
			listview.filter_area.add([
				["Item", "standard_rate", "=", "0"],
				// "=","0" بتتحول تلقائي لـ checkbox "Has Variants" الجاهز فوق
				// الصفحة (standard filter)، واللي بطبيعته مايقدرش يعبّر عن
				// "false" (بس "مفعّل" أو "من غير فلتر")، فالشرط كان بيتجاهل
				// بصمت. "!=","1" بتتفادى التحويل ده وتتحط كفلتر عادي شغال.
				["Item", "has_variants", "!=", "1"],
				["Item", "disabled", "=", "0"],
			]);
		});
	},
});
