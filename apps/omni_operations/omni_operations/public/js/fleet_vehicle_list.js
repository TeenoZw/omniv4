frappe.listview_settings["Fleet Vehicle"] = {
	add_fields: ["status", "vehicle_type", "customer", "odometer"],
	get_indicator(doc) {
		if (doc.status === "Inactive") {
			return [__("Inactive"), "gray", "status,=,Inactive"];
		}
		if (doc.status === "Maintenance") {
			return [__("Maintenance"), "orange", "status,=,Maintenance"];
		}
		return [__(doc.status || "Active"), "green", "status,=," + (doc.status || "Active")];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Active Vehicles"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "status", "=", "Active"]]);
		});
		listview.page.add_inner_button(__("Needs Maintenance"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "status", "=", "Maintenance"]]);
		});
	},
};
