frappe.ui.form.on("Customer Fleet Profile", {
	refresh(frm) {
		if (!frm.doc.name || frm.is_new()) {
			return;
		}

		frm.dashboard.set_headline(get_customer_next_step(frm));

		frm.add_custom_button(__("Open Portal View"), () => {
			window.open(`/omni_customer_portal?customer=${encodeURIComponent(frm.doc.customer)}`, "_blank");
		});
		frm.add_custom_button(__("Add Portal User"), () => {
			show_portal_user_dialog(frm);
		}, __("Customer Portal"));
		frm.add_custom_button(__("Vehicles"), () => {
			frappe.set_route("List", "Fleet Vehicle", { customer: frm.doc.customer });
		}, __("View"));
		frm.add_custom_button(__("Add Vehicle"), () => {
			frappe.new_doc("Fleet Vehicle", {
				customer: frm.doc.customer,
				company: frm.doc.company || frappe.defaults.get_default("Company"),
			});
		}, __("Next Step"));
		frm.add_custom_button(__("Prepare Kit"), () => {
			frappe.new_doc("Tracker SIM Assignment", {
				customer: frm.doc.customer,
				status: "Reserved",
			});
		}, __("Next Step"));
		frm.add_custom_button(__("Schedule Installation"), () => {
			frappe.new_doc("Tracker Installation", {
				customer: frm.doc.customer,
				company: frm.doc.company || frappe.defaults.get_default("Company"),
				status: "Scheduled",
			});
		}, __("Next Step"));
		frm.add_custom_button(__("Support"), () => {
			frappe.set_route("List", "Issue", { customer: frm.doc.customer });
		}, __("View"));
		frm.add_custom_button(__("Invoices"), () => {
			frappe.set_route("List", "Sales Invoice", { customer: frm.doc.customer });
		}, __("View"));
		frm.add_custom_button(__("Documents"), () => {
			frappe.set_route("List", "Fleet Document", { customer: frm.doc.customer });
		}, __("View"));
		frm.add_custom_button(__("Contracts"), () => {
			frappe.set_route("List", "Fleet Contract", { customer: frm.doc.customer });
		}, __("View"));

		frappe.call({
			method: "omni_operations.fleet.customer_360.get_customer_fleet_360",
			args: { customer: frm.doc.customer },
			callback(response) {
				const data = response.message;
				if (!data) {
					return;
				}

				frm.dashboard.add_indicator(
					__("Vehicles: {0}", [data.vehicles.length]),
					data.vehicles.length ? "blue" : "gray"
				);
				frm.dashboard.add_indicator(
					__("Invoice: {0}", [data.profile.invoice_status || "None"]),
					data.profile.invoice_outstanding_amount ? "orange" : "green"
				);
				frm.dashboard.add_indicator(
					__("Telematics Links: {0}", [data.telematics.length]),
					data.telematics.some((link) => link.sync_enabled) ? "green" : data.telematics.length ? "gray" : "gray"
				);
				if (data.summary.open_ticket_count) {
					frm.dashboard.add_indicator(
						__("Open Tickets: {0}", [data.summary.open_ticket_count]),
						"orange"
					);
				}
				frm.dashboard.add_indicator(
					__("Portal Documents: {0}", [data.summary.portal_document_count]),
					data.summary.portal_document_count ? "blue" : "gray"
				);
				frm.dashboard.add_indicator(
					__("Active Contracts: {0}", [data.summary.active_contract_count]),
					data.summary.active_contract_count ? "green" : "gray"
				);
			},
		});
	},
});

function get_customer_next_step(frm) {
	if (!frm.doc.total_vehicles) {
		return __("Customer hub is ready. Next: add the first vehicle.");
	}
	if (!frm.doc.active_trackers) {
		return __("Vehicles are captured. Next: prepare tracker/SIM kit or schedule installation.");
	}
	if (!frm.doc.latest_sales_invoice && !frm.doc.fleet_contract) {
		return __("Fleet is operational. Next: create contract or first invoice.");
	}
	return __("Customer is active. Use this page to manage vehicles, support, documents, contracts and billing.");
}

function show_portal_user_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Add Customer Portal User"),
		fields: [
			{
				fieldname: "full_name",
				fieldtype: "Data",
				label: __("Full Name"),
			},
			{
				fieldname: "email",
				fieldtype: "Data",
				label: __("Email"),
				options: "Email",
				reqd: 1,
			},
			{
				fieldname: "phone",
				fieldtype: "Data",
				label: __("Phone"),
			},
			{
				default: 1,
				fieldname: "send_welcome_email",
				fieldtype: "Check",
				label: __("Send welcome email"),
			},
		],
		primary_action_label: __("Create Portal Login"),
		primary_action(values) {
			frappe.call({
				method: "omni_operations.customer_portal.provisioning.create_customer_portal_user",
				args: {
					customer: frm.doc.customer,
					email: values.email,
					full_name: values.full_name,
					phone: values.phone,
					send_welcome_email: values.send_welcome_email ? 1 : 0,
				},
				freeze: true,
				freeze_message: __("Creating customer portal access..."),
				callback(response) {
					const result = response.message || {};
					frappe.show_alert({
						message: result.created ? __("Portal user created.") : __("Portal user already existed and was linked."),
						indicator: "green",
					});
					dialog.hide();
					frm.reload_doc();
				},
			});
		},
	});
	dialog.show();
}
