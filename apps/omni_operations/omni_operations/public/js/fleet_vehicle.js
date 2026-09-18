frappe.ui.form.on("Fleet Vehicle", {
	refresh(frm) {
		frm.set_df_property("registration_number", "hidden", 0);
		frm.set_df_property("registration_number", "read_only", frm.is_new() ? 0 : 1);
		if (!frm.doc.name || frm.is_new()) {
			return;
		}

		frm.add_custom_button(__("Change Registration Number"), () => {
			const dialog = new frappe.ui.Dialog({
				title: __("Change Vehicle Registration"),
				fields: [
					{
						fieldname: "registration_number",
						fieldtype: "Data",
						label: __("Registration Number"),
						reqd: 1,
						default: frm.doc.registration_number,
						description: __("This safely renames the vehicle and updates every linked Omni record."),
					},
				],
				primary_action_label: __("Update Registration"),
				primary_action(values) {
					frappe.call({
						method: "omni_operations.fleet.doctype.fleet_vehicle.fleet_vehicle.change_registration_number",
						args: { vehicle: frm.doc.name, registration_number: values.registration_number },
						freeze: true,
						freeze_message: __("Updating vehicle and linked records..."),
						callback(response) {
							const result = response.message || {};
							dialog.hide();
							frappe.show_alert({ message: __("Registration updated to {0}", [result.registration_number]), indicator: "green" });
							frappe.set_route("Form", "Fleet Vehicle", result.vehicle);
						},
					});
				},
			});
			dialog.show();
		}, __("Actions"));

		frm.trigger("show_telematics_status");
		frm.trigger("show_maintenance_status");
		frm.trigger("show_vehicle_360");
		frm.add_custom_button(
			__("Sync Telematics"),
			() => {
				frappe.call({
					method: "omni_operations.telematics.sync.sync_vehicle_telematics",
					args: { vehicle: frm.doc.name },
					freeze: true,
					freeze_message: __("Syncing telematics"),
					callback() {
						frm.reload_doc();
					},
				});
			},
			__("Telematics")
		);
		frm.add_custom_button(__("Telematics Links"), () => {
			frappe.set_route("List", "Telematics Unit Link", { vehicle: frm.doc.name });
		}, __("View"));
		frm.add_custom_button(__("Maintenance"), () => {
			frappe.set_route("List", "Fleet Maintenance Work Order", { vehicle: frm.doc.name });
		}, __("View"));
		frm.add_custom_button(__("Installations"), () => {
			frappe.set_route("List", "Tracker Installation", { vehicle: frm.doc.name });
		}, __("View"));
		frm.add_custom_button(__("Documents"), () => {
			frappe.set_route("List", "Fleet Document", { vehicle: frm.doc.name });
		}, __("View"));
		frm.add_custom_button(__("Contracts"), () => {
			frappe.set_route("List", "Fleet Contract", { vehicle: frm.doc.name });
		}, __("View"));
	},

	show_vehicle_360(frm) {
		frappe.call({
			method: "omni_operations.fleet.vehicle_360.get_vehicle_360",
			args: { vehicle: frm.doc.name },
			callback(response) {
				const data = response.message;
				if (!data) {
					return;
				}

				if (data.latest_invoice) {
					frm.dashboard.add_indicator(
						__("Invoice: {0}", [data.latest_invoice.status]),
						data.latest_invoice.outstanding_amount ? "orange" : "green"
					);
				}

				if (data.hub_assignment) {
					frm.dashboard.add_indicator(__("Hub: {0}", [data.hub_assignment.customer]), "blue");
				}
			},
		});
	},

	show_maintenance_status(frm) {
		frappe.call({
			method: "omni_operations.field_service.maintenance.get_vehicle_maintenance_status",
			args: { vehicle: frm.doc.name },
			callback(response) {
				const status = response.message;
				if (!status) {
					return;
				}

				frm.dashboard.add_indicator(
					__("Maintenance: {0}", [status.status]),
					status.indicator
				);
			},
		});
	},

	show_telematics_status(frm) {
		frappe.call({
			method: "omni_operations.telematics.status.get_vehicle_telematics_status",
			args: { vehicle: frm.doc.name },
			callback(response) {
				const status = response.message;
				if (!status) {
					return;
				}

				frm.dashboard.add_indicator(
					__("Telematics: {0}", [status.status]),
					status.indicator
				);

				if (status.message) {
					frm.dashboard.set_headline_alert(
						__("Telematics: {0}", [status.message]),
						status.indicator
					);
				}
			},
		});
	},
});
