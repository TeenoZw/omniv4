frappe.ui.form.on("Tracker Profile", {
	refresh(frm) {
		render_inventory_lifecycle(frm, "tracker");

		if (frm.is_new()) {
			frm.dashboard.set_headline(__("Add the tracker identity and stock item, then save before assigning it to a unit."));
			return;
		}

		frm.add_custom_button(__("Assign to Unit"), () => {
			open_unit_assignment_dialog(frm);
		}, __("Assignment"));
		frm.change_custom_button_type(__("Assign to Unit"), __("Assignment"), "primary");
		if (frm.doc.current_vehicle) {
			frm.add_custom_button(__("Return to Inventory"), () => {
				open_return_to_inventory_dialog(frm);
			}, __("Assignment"));
		}

		frm.add_custom_button(__("SIM Assignments"), () => {
			frappe.set_route("List", "Tracker SIM Assignment", { tracker: frm.doc.name });
		}, __("View"));

		frm.add_custom_button(__("Manage SIM Pairing"), () => {
			frappe.new_doc("Tracker SIM Assignment", {
				tracker: frm.doc.name,
				customer: frm.doc.current_customer,
				vehicle: frm.doc.current_vehicle,
				assigned_technician: frm.doc.assigned_technician,
			});
		}, __("Assignment"));

		if (frm.doc.current_vehicle) {
			frm.add_custom_button(__("Current Vehicle"), () => {
				frappe.set_route("Form", "Fleet Vehicle", frm.doc.current_vehicle);
			}, __("View"));
		}
	},
});

function open_unit_assignment_dialog(frm) {
	frappe.call({
		method: "omni_operations.tracker_inventory.doctype.tracker_profile.tracker_profile.get_assignment_context",
		args: { tracker: frm.doc.name },
		callback(response) {
			const context = response.message || {};
			const pairedSims = context.sims || [];
			let dialog;
			dialog = new frappe.ui.Dialog({
				title: __("Assign Tracker to Unit"),
				fields: [
					{
						fieldname: "unit",
						fieldtype: "Link",
						options: "Fleet Vehicle",
						label: __("Unit / Vehicle"),
						reqd: 1,
						default: context.unit,
						description: __("Choose the unit carrying this physical tracker."),
						change() {
							const unit = dialog.get_value("unit");
							if (!unit) {
								dialog.set_value("hub", null);
								return;
							}
							frappe.db.get_value("Fleet Vehicle", unit, "customer").then((result) => {
								dialog.set_value("hub", result.message ? result.message.customer : null);
							});
						},
					},
					{
						fieldname: "hub",
						fieldtype: "Link",
						options: "Customer",
						label: __("Customer Hub"),
						read_only: 1,
						default: context.hub,
						description: __("Filled automatically from the selected unit."),
					},
					{ fieldtype: "Section Break", label: __("Hardware Preparation") },
					{
						fieldname: "sim",
						fieldtype: "Link",
						options: "SIM Profile",
						label: __("SIM"),
						default: pairedSims[0],
						read_only: pairedSims.length > 0,
						reqd: pairedSims.length === 0,
						description: pairedSims.length
							? __("Existing pairing: {0}. Manage SIM Pairing to replace it.", [pairedSims.join(", ")])
							: __("Select the SIM prepared for this tracker."),
						get_query: () => ({ filters: { status: ["in", ["Available", "Prepared", "Reserved"]] } }),
					},
					{
						fieldname: "technician",
						fieldtype: "Link",
						options: "User",
						label: __("Technician"),
						default: context.technician,
					},
				],
				primary_action_label: __("Assign Tracker"),
				primary_action(values) {
					const assign = () => {
						frappe.call({
							method: "omni_operations.tracker_inventory.doctype.tracker_profile.tracker_profile.assign_to_unit",
							args: {
								tracker: frm.doc.name,
								vehicle: values.unit,
								sim: values.sim,
								technician: values.technician,
							},
							freeze: true,
							freeze_message: __("Assigning tracker to unit..."),
							callback(result) {
								if (!result.exc) {
									dialog.hide();
									frappe.show_alert({ message: __("Tracker assigned to {0}", [values.unit]), indicator: "green" });
									frm.reload_doc();
								}
							},
						});
					};

					if (context.unit && context.unit !== values.unit) {
						frappe.confirm(
							__("This tracker is currently assigned to {0}. Move it to {1}? The previous assignment will be closed.", [context.unit, values.unit]),
							assign
						);
						return;
					}
					assign();
				},
			});

			dialog.show();
		},
	});
}

function open_return_to_inventory_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Return Tracker to Inventory"),
		fields: [
			{
				fieldname: "current_unit",
				fieldtype: "Data",
				label: __("Current Unit / Vehicle"),
				default: frm.doc.current_vehicle,
				read_only: 1,
			},
			{
				fieldname: "condition",
				fieldtype: "Select",
				label: __("Condition on Return"),
				options: ["Used - Serviceable", "Needs Inspection", "Faulty", "Retired"],
				default: "Needs Inspection",
				reqd: 1,
				description: __("This closes the unit assignment. Installation history remains available."),
			},
		],
		primary_action_label: __("Return to Inventory"),
		primary_action(values) {
			frappe.call({
				method: "omni_operations.tracker_inventory.doctype.tracker_profile.tracker_profile.return_to_inventory",
				args: { tracker: frm.doc.name, condition: values.condition },
				freeze: true,
				freeze_message: __("Returning tracker to inventory..."),
				callback(result) {
					if (!result.exc) {
						dialog.hide();
						frappe.show_alert({ message: __("Tracker returned to inventory"), indicator: "green" });
						frm.reload_doc();
					}
				},
			});
		},
	});
	dialog.show();
}

function render_inventory_lifecycle(frm, kind) {
	const status = frm.doc.status || "In Stock";
	const condition = frm.doc.condition || "Brand New";
	frm.dashboard.add_indicator(__("Inventory: {0}", [status]), status === "Assigned" ? "blue" : "green");
	frm.dashboard.add_indicator(
		__("Condition: {0}", [condition]),
		["Brand New", "Used - Serviceable"].includes(condition) ? "green" : condition === "Needs Inspection" ? "orange" : "red"
	);

	const identifier = kind === "tracker" ? frm.doc.imei : frm.doc.iccid;
	const assignedTo = frm.doc.current_vehicle || frm.doc.current_customer || __("No customer assignment");
	frm.dashboard.set_headline(
		`${frappe.utils.escape_html(identifier || frm.doc.name)}: ` +
			`<b>${frappe.utils.escape_html(status)}</b> · ${frappe.utils.escape_html(condition)}<br>` +
			`${__("Current")}: ${frappe.utils.escape_html(assignedTo)}`
	);
}
