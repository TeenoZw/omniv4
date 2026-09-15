frappe.listview_settings["Fleet Contract"] = {
	add_fields: ["status", "customer", "vehicle", "billing_frequency", "monthly_rate", "next_billing_date", "billing_status"],
	get_indicator(doc) {
		if (doc.billing_status === "Overdue") {
			return [__("Overdue"), "red", "billing_status,=,Overdue"];
		}
		if (doc.status === "On Hold") {
			return [__("On Hold"), "orange", "status,=,On Hold"];
		}
		if (doc.status === "Expired" || doc.status === "Cancelled") {
			return [__(doc.status), "gray", "status,=," + doc.status];
		}
		return [__(doc.status || "Active"), "green", "status,=," + (doc.status || "Active")];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Active"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "status", "=", "Active"]]);
		});
		listview.page.add_inner_button(__("Due Soon"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "next_billing_date", "is", "set"]]);
		});
		listview.page.add_inner_button(__("Overdue"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "billing_status", "=", "Overdue"]]);
		});
	},
};
