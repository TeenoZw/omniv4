frappe.listview_settings["Telematics Discovered Account"] = {
	add_fields: ["activation_status", "customer", "duplicate_status"],
	onload(listview) {
		if (!listview.filter_area.get().length) {
			listview.filter_area.add([
				[listview.doctype, "account_type", "=", "Customer Hub"],
				[listview.doctype, "activation_status", "=", "Pending Verification"],
			]);
		}
		listview.page.add_inner_button(__("Show Hierarchy"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([[listview.doctype, "account_type", "in", ["Master Account", "Regional Admin"]]]);
			listview.refresh();
		});
		listview.page.add_inner_button(__("Show All"), () => {
			listview.filter_area.clear();
			listview.refresh();
		});
		listview.page.add_inner_button(__("Scan Duplicates"), () => {
			frappe.call({
				method: "omni_operations.telematics.sync.refresh_duplicate_matches",
				freeze: true,
				freeze_message: __("Checking existing customers..."),
				callback() { listview.refresh(); },
			});
		});
	},
	get_indicator(doc) {
		if (["Possible Duplicate", "Multiple Matches"].includes(doc.duplicate_status)) {
			return [__("Duplicate Warning"), "red", `duplicate_status,=,${doc.duplicate_status}`];
		}
		if (doc.activation_status === "Pending Verification") return [__("Pending Verification"), "orange", "activation_status,=,Pending Verification"];
		if (doc.activation_status === "Activated") return [__("Activated"), "green", "activation_status,=,Activated"];
		return [__(doc.activation_status), "gray", `activation_status,=,${doc.activation_status}`];
	},
};
