frappe.listview_settings["Omni Onboarding Job"] = {
	add_fields: ["status", "priority", "customer", "progress_percent", "target_go_live_date"],
	onload(listview) {
		listview.page.add_inner_button(__("Needs Action"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([
				["Omni Onboarding Job", "status", "not in", ["Active", "Lost", "Cancelled"]],
			]);
			listview.refresh();
		});

		listview.page.add_inner_button(__("Missing Customer"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([
				["Omni Onboarding Job", "customer_ready", "=", 0],
			]);
			listview.refresh();
		});

		listview.page.add_inner_button(__("Missing Vehicle"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([
				["Omni Onboarding Job", "customer_ready", "=", 1],
				["Omni Onboarding Job", "vehicles_ready", "=", 0],
				["Omni Onboarding Job", "status", "not in", ["Active", "Lost", "Cancelled"]],
			]);
			listview.refresh();
		});

		listview.page.add_inner_button(__("Ready for Install"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([
				["Omni Onboarding Job", "customer_ready", "=", 1],
				["Omni Onboarding Job", "vehicles_ready", "=", 1],
				["Omni Onboarding Job", "installation_ready", "=", 0],
				["Omni Onboarding Job", "status", "not in", ["Active", "Lost", "Cancelled"]],
			]);
			listview.refresh();
		});

		listview.page.add_inner_button(__("Portal/Billing"), () => {
			listview.filter_area.clear();
			listview.filter_area.add([
				["Omni Onboarding Job", "installation_ready", "=", 1],
				["Omni Onboarding Job", "status", "not in", ["Active", "Lost", "Cancelled"]],
			]);
			listview.refresh();
		});
	},
	get_indicator(doc) {
		const status = doc.status || "New";
		const colorMap = {
			New: "blue",
			Qualification: "orange",
			Quotation: "orange",
			"Customer Setup": "purple",
			"Vehicle Setup": "purple",
			Installation: "orange",
			"Portal Provisioning": "blue",
			"Billing Readiness": "yellow",
			Active: "green",
			"On Hold": "gray",
			Lost: "red",
			Cancelled: "red",
		};

		return [status, colorMap[status] || "gray", `status,=,${status}`];
	},
};
