frappe.listview_settings["Telematics Unit Link"] = {
	add_fields: ["status", "sync_enabled", "last_sync_status", "customer", "vehicle", "provider"],
	get_indicator(doc) {
		if (!doc.sync_enabled) {
			return [__("Sync Off"), "gray", "sync_enabled,=,0"];
		}
		const color = {
			Success: "green",
			Warning: "orange",
			Failed: "red",
			"Never Synced": "gray",
		}[doc.last_sync_status] || "blue";
		return [__(doc.last_sync_status || "Never Synced"), color, "last_sync_status,=," + (doc.last_sync_status || "Never Synced")];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Sync Off"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "sync_enabled", "=", 0]]);
		});
		listview.page.add_inner_button(__("Failed Sync"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "last_sync_status", "=", "Failed"]]);
		});
	},
};
