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
		frm.add_custom_button(__("Manage Portal Users"), () => {
			show_portal_users(frm);
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

function show_portal_users(frm) {
	frappe.call({
		method: "omni_operations.customer_portal.provisioning.get_customer_portal_users",
		args: { customer: frm.doc.customer },
		freeze: true,
		callback(response) {
			const users = response.message?.users || [];
			const rows = users.length
				? users.map((user) => `
					<tr>
						<td>${frappe.utils.escape_html(user.full_name || user.name)}</td>
						<td>${frappe.utils.escape_html(user.name)}</td>
						<td>${user.enabled ? __("Active") : __("Disabled")}</td>
						<td class="text-nowrap">
							<button class="btn btn-xs btn-default omni-reset-user" data-user="${frappe.utils.escape_html(user.name)}">${__("Reset Password")}</button>
							<button class="btn btn-xs btn-danger omni-revoke-user" data-user="${frappe.utils.escape_html(user.name)}">${__("Revoke")}</button>
						</td>
					</tr>`).join("")
				: `<tr><td colspan="4" class="text-muted">${__("No portal users are linked to this customer.")}</td></tr>`;
			const dialog = new frappe.ui.Dialog({
				title: __("Portal Users for {0}", [frm.doc.customer]),
				fields: [{
					fieldname: "users_html",
					fieldtype: "HTML",
					options: `<div class="table-responsive"><table class="table table-bordered">
						<thead><tr><th>${__("Name")}</th><th>${__("Email")}</th><th>${__("Status")}</th><th></th></tr></thead>
						<tbody>${rows}</tbody></table></div>`,
				}],
				primary_action_label: __("Add Portal User"),
				primary_action() {
					dialog.hide();
					show_portal_user_dialog(frm);
				},
			});
			dialog.$wrapper.on("click", ".omni-revoke-user", function () {
				const email = this.dataset.user;
				frappe.confirm(
					__("Remove {0}'s access to {1}?", [email, frm.doc.customer]),
					() => frappe.call({
						method: "omni_operations.customer_portal.provisioning.revoke_customer_portal_user",
						args: { customer: frm.doc.customer, email },
						freeze: true,
						callback() {
							dialog.hide();
							frappe.show_alert({ message: __("Portal access revoked."), indicator: "green" });
							show_portal_users(frm);
						},
					})
				);
			});
			dialog.$wrapper.on("click", ".omni-reset-user", function () {
				const email = this.dataset.user;
				frappe.call({
					method: "omni_operations.customer_portal.provisioning.send_portal_password_reset",
					args: { customer: frm.doc.customer, email },
					freeze: true,
					freeze_message: __("Sending password reset email..."),
					callback() {
						frappe.show_alert({ message: __("Password reset email sent."), indicator: "green" });
					},
				});
			});
			dialog.show();
		},
	});
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
			{
				default: 0,
				fieldname: "reassign",
				fieldtype: "Check",
				label: __("Reassign from another customer"),
				description: __("Removes this user's access to their previous customer. Use only after confirming the change."),
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
					reassign: values.reassign ? 1 : 0,
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
