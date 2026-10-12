frappe.ui.form.on("Item", {
	refresh(frm) {
		if (!frm.doc.has_variants || frm.is_new()) return;
		render_variant_prices_grid(frm);
	},
});

function render_variant_prices_grid(frm) {
	const field = frm.fields_dict.custom_variant_prices_html;
	if (!field) return;

	const $wrapper = $(field.$wrapper).empty();
	const $loading = $(`<p class="text-muted">${__("جاري التحميل...")}</p>`).appendTo($wrapper);

	frappe.call({
		method: "loyalpet.api.items.get_template_variant_prices",
		args: { template: frm.doc.name },
		callback(r) {
			$loading.remove();
			build_grid(frm, $wrapper, r.message || []);
		},
	});
}

function build_grid(frm, $wrapper, variants) {
	if (!variants.length) {
		$wrapper.append(
			`<p class="text-muted">${__("لا يوجد Variants لهذا المنتج بعد.")}</p>`
		);
		return;
	}

	const $table = $(`
		<table class="table table-bordered" style="margin-top: 10px;">
			<thead>
				<tr>
					<th>${__("كود الصنف")}</th>
					<th>${__("الخصائص")}</th>
					<th style="width: 180px;">${__("السعر")}</th>
				</tr>
			</thead>
			<tbody></tbody>
		</table>
	`).appendTo($wrapper);

	const $tbody = $table.find("tbody");

	variants.forEach((v) => {
		$(`
			<tr>
				<td>
					<a href="/app/item/${encodeURIComponent(v.item_code)}" target="_blank">${frappe.utils.escape_html(v.item_code)}</a>
					<div class="text-muted small">${frappe.utils.escape_html(v.item_name || "")}</div>
				</td>
				<td>${frappe.utils.escape_html(v.attributes_label || "")}</td>
				<td>
					<input type="number" step="0.01" class="form-control variant-price-input"
						data-item-code="${frappe.utils.escape_html(v.item_code)}"
						value="${v.standard_rate || 0}">
				</td>
			</tr>
		`).appendTo($tbody);
	});

	const $save_row = $(`<div style="margin-top: 10px;"></div>`).appendTo($wrapper);
	const $save_btn = $(`<button class="btn btn-primary btn-sm">${__("حفظ الأسعار")}</button>`).appendTo(
		$save_row
	);

	$save_btn.on("click", () => {
		const prices = [];
		$wrapper.find(".variant-price-input").each(function () {
			prices.push({
				item_code: $(this).attr("data-item-code"),
				rate: parseFloat($(this).val()) || 0,
			});
		});

		$save_btn.prop("disabled", true).text(__("جاري الحفظ..."));
		frappe.call({
			method: "loyalpet.api.items.bulk_update_variant_prices",
			args: { prices },
			callback(r) {
				$save_btn.prop("disabled", false).text(__("حفظ الأسعار"));
				const updated = (r.message && r.message.updated) || [];
				frappe.show_alert({
					message: __("تم تحديث {0} صنف", [updated.length]),
					indicator: "green",
				});
				render_variant_prices_grid(frm);
			},
			error() {
				$save_btn.prop("disabled", false).text(__("حفظ الأسعار"));
			},
		});
	});
}
