frappe.query_reports["Wallet Transactions"] = {
	filters: [
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "type",
			label: __("Type"),
			fieldtype: "Select",
			options: "\ncredit\ndebit",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "type" && data) {
			const color = data.type === "credit" ? "green" : "red";
			value = `<span style="color: var(--${color}-500); font-weight: 600;">${data.type}</span>`;
		}
		if (column.fieldname === "status" && data) {
			const color = { Completed: "green", Pending: "orange", Reversed: "red" }[data.status] || "gray";
			value = `<span class="indicator-pill ${color}">${data.status}</span>`;
		}
		return value;
	},
};
