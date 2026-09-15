frappe.listview_settings["Tracker SIM Assignment"] = {
	add_fields: ["status", "slot", "tracker", "sim", "customer", "vehicle"],
	get_indicator(doc) {
		const color = {
			Prepared: "blue",
			Reserved: "yellow",
			Assigned: "orange",
			Installed: "green",
			Removed: "gray",
			Cancelled: "gray",
		}[doc.status] || "gray";
		return [__(doc.status || "Prepared"), color, "status,=," + (doc.status || "Prepared")];
	},
	onload(listview) {
		for (const status of ["Prepared", "Reserved", "Assigned", "Installed"]) {
			listview.page.add_inner_button(__(status), () => {
				listview.filter_area.clear();
				listview.filter_area.add([[listview.doctype, "status", "=", status]]);
			});
		}
	},
};
