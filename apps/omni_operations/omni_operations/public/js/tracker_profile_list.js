frappe.listview_settings["Tracker Profile"] = {
	add_fields: ["status", "tracker_name", "item_code", "current_customer", "current_vehicle"],
	get_indicator(doc) {
		const color = {
			Available: "green",
			Prepared: "blue",
			Reserved: "yellow",
			Assigned: "orange",
			Installed: "green",
			Faulty: "red",
			Returned: "gray",
			Retired: "gray",
		}[doc.status] || "gray";
		return [__(doc.status || "Available"), color, `status,=,${doc.status || "Available"}`];
	},
	onload(listview) {
		listview.page.set_primary_action(__("Add Tracker"), () => frappe.new_doc("Tracker Profile"), "add");
		listview.page.add_inner_button(__("Available"), () => apply_tracker_filter(listview, "Available"));
		listview.page.add_inner_button(__("Assigned / Installed"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "status", "in", ["Assigned", "Installed"]]]);
		});
	},
};

function apply_tracker_filter(listview, status) {
	listview.filter_area.clear();
	listview.filter_area.add([[listview.doctype, "status", "=", status]]);
}
