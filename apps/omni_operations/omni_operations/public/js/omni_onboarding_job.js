frappe.ui.form.on("Omni Onboarding Job", {
	refresh(frm) {
		frm.dashboard.clear_headline();
		render_onboarding_summary(frm);

		if (frm.is_new()) {
			frm.dashboard.set_headline(__("Step 1: enter the client or hub name and contact details. Save, then complete prerequisites from top to bottom."));
			return;
		}

		frm.add_custom_button(__("Create Customer/Hub"), () => {
			call_onboarding_action(frm, "ensure_customer_hub", __("Customer/hub is ready."));
		}, __("Prerequisites"));

		frm.add_custom_button(__("Create Fleet Profile"), () => {
			call_onboarding_action(frm, "ensure_fleet_profile", __("Fleet profile is ready."));
		}, __("Prerequisites"));

		frm.add_custom_button(__("Add Vehicle"), () => {
			show_vehicle_dialog(frm);
		}, __("Prerequisites"));

		frm.add_custom_button(__("Prepare Tracker/SIM Kit"), () => {
			if (!frm.doc.customer) {
				frappe.msgprint(__("Create the customer/hub first so the kit can be reserved against the correct client."));
				return;
			}
			frappe.new_doc("Tracker SIM Assignment", {
				customer: frm.doc.customer,
				vehicle: frm.doc.primary_vehicle,
				assigned_technician: frm.doc.installation_coordinator,
				status: frm.doc.primary_vehicle ? "Assigned" : "Reserved",
			});
		}, __("Prerequisites"));

		frm.add_custom_button(__("Schedule Installation"), () => {
			if (!frm.doc.customer || !frm.doc.primary_vehicle) {
				frappe.msgprint(__("Create the customer/hub and add at least one vehicle before scheduling installation."));
				return;
			}
			frappe.new_doc("Tracker Installation", {
				customer: frm.doc.customer,
				company: frm.doc.company || frappe.defaults.get_default("Company"),
				vehicle: frm.doc.primary_vehicle,
				installation_coordinator: frm.doc.installation_coordinator,
				status: "Scheduled",
			});
		}, __("Prerequisites"));

		frm.add_custom_button(__("Provision Portal User"), () => {
			call_onboarding_action(frm, "provision_portal_user", __("Portal user is ready."));
		}, __("Customer Access"));

		frm.add_custom_button(__("Complete Onboarding"), () => {
			call_onboarding_action(frm, "complete_onboarding", __("Onboarding marked active."));
		}, __("Finish"));

		add_related_buttons(frm);
	},
});

function render_onboarding_summary(frm) {
	const progress = Math.round(frm.doc.progress_percent || 0);
	const status = frm.doc.status || __("New");
	const customer = frm.doc.customer || __("Customer/hub not created yet");
	const nextAction = frm.doc.next_action || get_onboarding_next_step(frm);

	frm.dashboard.set_headline(
		`${__("Status")}: <b>${frappe.utils.escape_html(status)}</b> &nbsp; ` +
			`${__("Progress")}: <b>${progress}%</b> &nbsp; ` +
			`${__("Customer")}: <b>${frappe.utils.escape_html(customer)}</b><br>` +
			`${__("Next")}: ${frappe.utils.escape_html(nextAction)}`
	);

	const checks = [
		["customer_ready", __("Customer")],
		["customer_fleet_profile", __("Fleet Profile")],
		["vehicles_ready", __("Vehicles")],
		["installation_ready", __("Installation")],
		["portal_ready", __("Portal")],
		["lead_qualified", __("Lead")],
		["quotation_ready", __("Quotation")],
		["billing_ready", __("Billing")],
	];

	checks.forEach(([fieldname, label]) => {
		frm.dashboard.add_indicator(label, frm.doc[fieldname] ? "green" : "gray");
	});
}

function get_onboarding_next_step(frm) {
	if (!frm.doc.customer_ready) {
		return __("Step 1: create or confirm the customer/hub record.");
	}
	if (!frm.doc.customer_fleet_profile) {
		return __("Step 2: create the customer fleet profile.");
	}
	if (!frm.doc.vehicles_ready) {
		return __("Step 3: add the vehicles that need tracking.");
	}
	if (!frm.doc.installation_ready) {
		return __("Step 4: prepare the tracker/SIM kit and schedule installation.");
	}
	if (!frm.doc.portal_ready) {
		return __("Step 5: provision the customer portal user.");
	}
	if (!frm.doc.lead_qualified) {
		return __("Step 6: qualify or link the lead for sales traceability.");
	}
	if (!frm.doc.quotation_ready) {
		return __("Step 7: prepare the quotation or proposal.");
	}
	if (!frm.doc.billing_ready) {
		return __("Step 8: prepare invoice, payment or billing agreement.");
	}
	return __("All readiness steps are complete. Mark onboarding active.");
}

function call_onboarding_action(frm, action, successMessage) {
	frappe.call({
		method: `omni_operations.onboarding.doctype.omni_onboarding_job.omni_onboarding_job.${action}`,
		args: { job: frm.doc.name },
		freeze: true,
		freeze_message: __("Updating onboarding records..."),
		callback(response) {
			if (response.message) {
				frappe.show_alert({ message: successMessage, indicator: "green" });
				frm.reload_doc();
			}
		},
	});
}

function show_vehicle_dialog(frm) {
	if (!frm.doc.customer) {
		frappe.msgprint(__("Create the customer/hub first. The vehicle will then be linked to the right client automatically."));
		return;
	}

	const dialog = new frappe.ui.Dialog({
		title: __("Add Customer Vehicle"),
		fields: [
			{
				fieldname: "registration_number",
				fieldtype: "Data",
				label: __("Registration Number"),
				reqd: 1,
			},
			{
				fieldname: "vehicle_name",
				fieldtype: "Data",
				label: __("Vehicle Name"),
				description: __("Optional. Leave blank to use the registration number."),
			},
			{
				fieldname: "vehicle_type",
				fieldtype: "Select",
				label: __("Vehicle Type"),
				options: "Car\nTruck\nBus\nVan\nMotorcycle\nTrailer\nPlant Equipment\nOther",
				default: "Car",
			},
			{ fieldname: "details_section", fieldtype: "Section Break", label: __("Optional Details") },
			{ fieldname: "make", fieldtype: "Data", label: __("Make") },
			{ fieldname: "model", fieldtype: "Data", label: __("Model") },
			{ fieldname: "column_break", fieldtype: "Column Break" },
			{ fieldname: "year", fieldtype: "Int", label: __("Year") },
			{ fieldname: "vin", fieldtype: "Data", label: __("VIN") },
			{ fieldname: "odometer", fieldtype: "Float", label: __("Odometer") },
		],
		primary_action_label: __("Add Vehicle"),
		primary_action(values) {
			frappe.call({
				method: "omni_operations.onboarding.doctype.omni_onboarding_job.omni_onboarding_job.create_vehicle_for_onboarding",
				args: {
					job: frm.doc.name,
					...values,
				},
				freeze: true,
				freeze_message: __("Adding vehicle..."),
				callback(response) {
					if (response.message) {
						dialog.hide();
						frappe.show_alert({ message: __("Vehicle is ready."), indicator: "green" });
						frm.reload_doc();
					}
				},
			});
		},
	});

	dialog.show();
}

function add_related_buttons(frm) {
	frm.add_custom_button(__("Lead"), () => {
		if (frm.doc.lead) {
			frappe.set_route("Form", "Lead", frm.doc.lead);
		} else {
			frappe.new_doc("Lead", {
				lead_name: frm.doc.contact_name || frm.doc.prospect_name,
				company_name: frm.doc.prospect_name,
				email_id: frm.doc.contact_email,
				mobile_no: frm.doc.contact_phone,
				source: frm.doc.source || "Website",
			});
		}
	}, __("Sales"));

	frm.add_custom_button(__("Vehicle"), () => {
		if (frm.doc.primary_vehicle) {
			frappe.set_route("Form", "Fleet Vehicle", frm.doc.primary_vehicle);
		} else {
			show_vehicle_dialog(frm);
		}
	}, __("View"));

	frm.add_custom_button(__("Installation"), () => {
		if (frm.doc.primary_installation) {
			frappe.set_route("Form", "Tracker Installation", frm.doc.primary_installation);
		} else {
			frappe.set_route("List", "Tracker Installation", { customer: frm.doc.customer });
		}
	}, __("View"));

	frm.add_custom_button(__("Tracker/SIM Kit"), () => {
		frappe.set_route("List", "Tracker SIM Assignment", { customer: frm.doc.customer });
	}, __("View"));

	frm.add_custom_button(__("Quotation"), () => {
		if (frm.doc.quotation) {
			frappe.set_route("Form", "Quotation", frm.doc.quotation);
		} else {
			frappe.set_route("List", "Quotation", { party_name: frm.doc.customer });
		}
	}, __("Sales"));

	frm.add_custom_button(__("Fleet Profile"), () => {
		if (frm.doc.customer_fleet_profile) {
			frappe.set_route("Form", "Customer Fleet Profile", frm.doc.customer_fleet_profile);
		} else if (frm.doc.customer) {
			frappe.set_route("List", "Customer Fleet Profile", { customer: frm.doc.customer });
		}
	}, __("View"));

	frm.add_custom_button(__("Portal"), () => {
		if (frm.doc.customer) {
			window.open(`/omni_customer_portal?customer=${encodeURIComponent(frm.doc.customer)}`, "_blank");
		}
	}, __("View"));
}
