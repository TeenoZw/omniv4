frappe.listview_settings["Tracker Profile"] = {
	add_fields: ["status", "condition", "tracker_name", "item_code", "current_customer", "current_vehicle"],
	get_indicator(doc) {
		const serviceable = ["Brand New", "Used - Serviceable"].includes(doc.condition);
		const color = !serviceable ? "red" : doc.status === "Assigned" ? "blue" : "green";
		const label = `${doc.status || "In Stock"} · ${doc.condition || "Brand New"}`;
		return [__(label), color, `status,=,${doc.status || "In Stock"}`];
	},
	onload(listview) {
		listview.page.set_primary_action(__("Add Tracker"), () => frappe.new_doc("Tracker Profile"), "add");
		listview.page.add_inner_button(__("Ready to Assign"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([
				[listview.doctype, "status", "=", "In Stock"],
				[listview.doctype, "condition", "in", ["Brand New", "Used - Serviceable"]],
			]);
		});
		listview.page.add_inner_button(__("Assigned"), () => apply_tracker_filter(listview, "Assigned"));
		listview.page.add_inner_button(__("Needs Attention"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "condition", "in", ["Needs Inspection", "Faulty"]]]);
		});
	},
};

function apply_tracker_filter(listview, status) {
	listview.filter_area.clear();
	listview.filter_area.add([[listview.doctype, "status", "=", status]]);
}
