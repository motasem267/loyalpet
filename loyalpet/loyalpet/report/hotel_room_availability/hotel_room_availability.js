frappe.query_reports["Hotel Room Availability"] = {
	filters: [
		{
			fieldname: "date",
			label: __("Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "availability_status" && data) {
			const color = {
				"Available": "green",
				"Checked In": "blue",
				"Confirmed": "orange",
			}[data.availability_status] || "gray";
			value = `<span class="indicator-pill ${color}">${data.availability_status}</span>`;
		}
		return value;
	},
};
