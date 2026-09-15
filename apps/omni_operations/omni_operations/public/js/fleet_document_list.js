frappe.listview_settings["Fleet Document"] = {
	add_fields: ["status", "document_type", "customer", "vehicle", "expiry_date", "portal_visible"],
	get_indicator(doc) {
		if (doc.status === "Expired") {
			return [__("Expired"), "red", "status,=,Expired"];
		}
		if (!doc.portal_visible) {
			return [__("Internal"), "gray", "portal_visible,=,0"];
		}
		return [__(doc.status || "Active"), "green", "status,=," + (doc.status || "Active")];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Portal Visible"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "portal_visible", "=", 1]]);
		});
		listview.page.add_inner_button(__("Expiring"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "expiry_date", "is", "set"]]);
		});
	},
};
