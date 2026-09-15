frappe.listview_settings["Tracker Installation"] = {
	add_fields: ["status", "scheduled_date", "customer", "vehicle", "technician"],
	get_indicator(doc) {
		const color = {
			Scheduled: "blue",
			"In Progress": "orange",
			Completed: "green",
			Cancelled: "gray",
			Failed: "red",
		}[doc.status] || "gray";
		return [__(doc.status || "Draft"), color, "status,=," + (doc.status || "Draft")];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Scheduled"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "status", "=", "Scheduled"]]);
		});
		listview.page.add_inner_button(__("In Progress"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "status", "=", "In Progress"]]);
		});
	},
};
