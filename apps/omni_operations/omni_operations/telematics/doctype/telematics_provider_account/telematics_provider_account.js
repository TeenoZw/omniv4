frappe.ui.form.on("Telematics Provider Account", {
	refresh(frm) {
		set_scope_controls(frm);

		if (frm.is_new()) {
			return;
		}

		frm.add_custom_button(__("Check Connection"), () => {
			frappe.call({
				method: "omni_operations.telematics.sync.check_provider_connection",
				args: {
					provider_account_name: frm.doc.name,
				},
				freeze: true,
				freeze_message: __("Checking provider connection..."),
				callback(response) {
					const result = response.message || {};
					frm.reload_doc();
					if (result.status === "Success") {
						frappe.show_alert({ message: __("Connection successful"), indicator: "green" });
					} else {
						frappe.msgprint({
							title: __("Connection failed"),
							indicator: "red",
							message: result.error_message || __("The provider connection check failed."),
						});
					}
				},
			});
		});

		frm.add_custom_button(__("Preview Units"), () => {
			frappe.call({
				method: "omni_operations.telematics.sync.preview_provider_units",
				args: {
					provider_account_name: frm.doc.name,
				},
				freeze: true,
				freeze_message: __("Loading provider units..."),
				callback(response) {
					const result = response.message || {};
					const units = result.units || [];
					const rows = units.map((unit) => `
						<tr>
							<td>${frappe.utils.escape_html(unit.external_unit_name || "")}</td>
							<td>${frappe.utils.escape_html(unit.external_unit_id || "")}</td>
							<td>${frappe.utils.escape_html(unit.external_imei || "")}</td>
							<td>${unit.ignored ? __("Ignored") : unit.matched ? __("Matched") : __("Needs Link")}</td>
							<td>${frappe.utils.escape_html(unit.vehicle || "")}</td>
						</tr>
					`).join("");
					frappe.msgprint({
						title: __("Provider Units"),
						indicator: result.unmatched_units ? "orange" : "green",
						message: `
							<p>${__("Total {0}; matched {1}; ignored {2}; unmatched {3}.", [
								result.total_units || 0,
								result.matched_units || 0,
								result.ignored_units || 0,
								result.unmatched_units || 0,
							])}</p>
							<table class="table table-bordered">
								<thead>
									<tr>
										<th>${__("Unit")}</th>
										<th>${__("External ID")}</th>
										<th>${__("IMEI")}</th>
										<th>${__("Status")}</th>
										<th>${__("Vehicle")}</th>
									</tr>
								</thead>
								<tbody>${rows || `<tr><td colspan="5">${__("No units returned.")}</td></tr>`}</tbody>
							</table>
						`,
					});
				},
			});
		});

		frm.add_custom_button(__("Sync Units"), () => {
			frappe.call({
				method: "omni_operations.telematics.sync.sync_provider_units",
				args: {
					provider_account_name: frm.doc.name,
				},
				freeze: true,
				freeze_message: __("Syncing telematics units..."),
				callback(response) {
					const result = response.message || {};
					frm.reload_doc();
					frappe.msgprint({
						title: __("Unit sync {0}", [result.status || "Complete"]),
						indicator: result.status === "Success" ? "green" : "orange",
						message: __("Processed {0}; updated {1}; failed {2}.", [
							result.records_processed || 0,
							result.records_updated || 0,
							result.records_failed || 0,
						]),
					});
				},
			});
		});
	},

	account_scope(frm) {
		set_scope_controls(frm);
	},
});

function set_scope_controls(frm) {
	const is_customer_hub = frm.doc.account_scope === "Customer Hub";
	frm.toggle_reqd("customer", is_customer_hub);
	frm.toggle_display("customer", is_customer_hub);
	frm.toggle_display("parent_provider_account", frm.doc.account_scope !== "System-wide");
	frm.toggle_display("region", frm.doc.account_scope === "Regional Admin");

	if (!is_customer_hub && frm.doc.customer) {
		frm.set_value("customer", null);
	}
}
