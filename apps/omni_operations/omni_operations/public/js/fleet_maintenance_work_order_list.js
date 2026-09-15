frappe.listview_settings["Fleet Maintenance Work Order"] = {
	add_fields: ["status", "priority", "scheduled_date", "customer", "vehicle", "billing_status"],
	get_indicator(doc) {
		if (doc.priority === "Urgent" && !["Completed", "Cancelled"].includes(doc.status)) {
			return [__("Urgent"), "red", "priority,=,Urgent"];
		}
		const color = {
			Open: "blue",
			Scheduled: "blue",
			"In Progress": "orange",
			Completed: "green",
			Cancelled: "gray",
		}[doc.status] || "gray";
		return [__(doc.status || "Open"), color, "status,=," + (doc.status || "Open")];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Open Work"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "status", "not in", ["Completed", "Cancelled"]]]);
		});
		listview.page.add_inner_button(__("Billable"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "billing_status", "!=", "Invoiced"]]);
		});
	},
};
