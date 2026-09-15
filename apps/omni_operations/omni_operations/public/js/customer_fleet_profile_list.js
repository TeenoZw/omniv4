frappe.listview_settings["Customer Fleet Profile"] = {
	add_fields: ["status", "invoice_status", "invoice_outstanding_amount", "total_vehicles", "active_trackers"],
	get_indicator(doc) {
		if (doc.invoice_outstanding_amount > 0) {
			return [__("Outstanding"), "orange", "invoice_outstanding_amount,>,0"];
		}
		if (doc.status === "Suspended") {
			return [__("Suspended"), "red", "status,=,Suspended"];
		}
		return [__(doc.status || "Active"), "green", "status,=," + (doc.status || "Active")];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Active Customers"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "status", "=", "Active"]]);
		});
		listview.page.add_inner_button(__("Outstanding"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "invoice_outstanding_amount", ">", 0]]);
		});
	},
};
