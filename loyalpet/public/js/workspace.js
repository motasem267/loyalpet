// LoyalPet – add icons to workspace shortcut buttons
frappe.provide("loyalpet");

const SHORTCUT_ICONS = {
	"Wallet": "money-coins-1",
	"Wallet Transaction": "expenses",
	"Voucher": "tag",
	"Vet Service Type": "clipboard",
	"Vet Appointment": "calendar",
	"Hotel Room Type": "list",
	"Hotel Room Service": "star",
	"Hotel Room": "organization",
	"Hotel Booking": "calendar",
};

loyalpet.inject_shortcut_icons = function () {
	$(".shortcut-widget-box").each(function () {
		const $widget = $(this);
		if ($widget.find(".lp-icon").length) return;
		const name = $widget.attr("data-widget-name");
		const icon_name = SHORTCUT_ICONS[name];
		if (!icon_name) return;
		const svg = frappe.utils.icon(icon_name, "md");
		$widget
			.find(".widget-title")
			.prepend(`<span class="lp-icon" style="margin-right:8px;vertical-align:middle;">${svg}</span>`);
	});
};

$(document).on("page-change", function () {
	const route = frappe.get_route();
	if (route && route[0] === "Workspaces") {
		// workspace renders asynchronously; wait for DOM
		setTimeout(loyalpet.inject_shortcut_icons, 600);
	}
});
