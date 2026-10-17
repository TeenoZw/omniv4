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
		frm.trigger("show_tracker_status");
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
		frm.add_custom_button(__("Assign Tracker"), () => {
			open_tracker_assignment_dialog(frm);
		}, __("Assignment"));
		frm.change_custom_button_type(__("Assign Tracker"), __("Assignment"), "primary");
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

	show_tracker_status(frm) {
		frappe.db.get_list("Tracker Profile", {
			filters: { current_vehicle: frm.doc.name },
			fields: ["name", "status"],
			limit: 5,
		}).then((trackers) => {
			if (!trackers.length) {
				frm.dashboard.add_indicator(__("Tracker: Not assigned"), "gray");
				return;
			}
			const tracker = trackers[0];
			frm.dashboard.add_indicator(__("Tracker: {0} ({1})", [tracker.name, tracker.status]), "blue");
		});
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

function open_tracker_assignment_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Assign Tracker to {0}", [frm.doc.name]),
		fields: [
			{
				fieldname: "hub",
				fieldtype: "Link",
				options: "Customer",
				label: __("Customer Hub"),
				default: frm.doc.customer,
				read_only: 1,
			},
			{
				fieldname: "tracker",
				fieldtype: "Link",
				options: "Tracker Profile",
				label: __("Tracker"),
				reqd: 1,
				description: __("Choose an available/prepared tracker, or the tracker already assigned to this unit."),
				get_query: () => ({
					filters: { status: ["in", ["Available", "Prepared", "Reserved", "Assigned", "Installed"]] },
				}),
			},
			{
				fieldname: "sim",
				fieldtype: "Link",
				options: "SIM Profile",
				label: __("SIM (if not already paired)"),
				get_query: () => ({ filters: { status: ["in", ["Available", "Prepared", "Reserved"]] } }),
			},
			{
				fieldname: "technician",
				fieldtype: "Link",
				options: "User",
				label: __("Technician"),
			},
		],
		primary_action_label: __("Assign Tracker"),
		primary_action(values) {
			frappe.call({
				method: "omni_operations.tracker_inventory.doctype.tracker_profile.tracker_profile.assign_to_unit",
				args: {
					tracker: values.tracker,
					vehicle: frm.doc.name,
					sim: values.sim,
					technician: values.technician,
				},
				freeze: true,
				freeze_message: __("Assigning tracker to unit..."),
				callback(result) {
					if (!result.exc) {
						dialog.hide();
						frappe.show_alert({ message: __("Tracker assigned"), indicator: "green" });
						frm.reload_doc();
					}
				},
			});
		},
	});
	dialog.show();
}
