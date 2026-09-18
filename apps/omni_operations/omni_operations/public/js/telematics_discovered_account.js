frappe.ui.form.on("Telematics Discovered Account", {
	refresh(frm) {
		if (frm.is_new()) return;
		const is_customer_hub = frm.doc.account_type === "Customer Hub";
		if (!is_customer_hub) {
			frm.dashboard.set_headline_alert(
				__("Structural telematics account retained for hierarchy mapping. No customer activation is required."),
				"blue"
			);
			return;
		}
		if (["Possible Duplicate", "Multiple Matches"].includes(frm.doc.duplicate_status)) {
			frm.dashboard.set_headline_alert(
				__("Possible duplicate customer detected: {0}", [frm.doc.duplicate_candidates || frm.doc.suggested_existing_customer]),
				"orange"
			);
			frm.add_custom_button(__("Resolve Duplicate"), () => show_duplicate_dialog(frm), __("Onboarding"));
		}
		if (frm.doc.activation_status === "Ignored") return;
		if (frm.doc.activation_status === "Activated") {
			frm.add_custom_button(__("Reconcile Wialon Vehicles"), () => frappe.call({
				method: "omni_operations.telematics.sync.link_approved_account_units",
				args: { discovered_account_name: frm.doc.name }, freeze: true,
				freeze_message: __("Matching Wialon units to vehicles..."),
				callback(response) {
					const result = response.message || {};
					frappe.msgprint(__("Processed {0}; linked {1}; created {2}; conflicts {3}.", [
						result.processed || 0, (result.linked || []).length, (result.created || []).length,
						(result.conflicts || []).length,
					]));
				},
			}), __("Onboarding"));
			return;
		}
		frm.add_custom_button(__("Verify and Activate"), () => {
			frappe.confirm(
				__("Approve {0}, create or link its customer profile, then automatically match or create vehicles for units owned by this Wialon account? Existing vehicle ownership will never be changed automatically.", [frm.doc.account_name]),
				() => frappe.call({
					method: "omni_operations.telematics.sync.activate_discovered_account",
					args: { discovered_account_name: frm.doc.name }, freeze: true,
					freeze_message: __("Activating Omni customer account..."),
					callback(response) {
						const result = response.message || {};
						const imported = result.vehicle_import || {};
						const message = __("Customer {0} activated. {1} unit(s) linked, {2} vehicle(s) created, {3} conflict(s) held for review.", [
							result.customer, (imported.linked || []).length, (imported.created || []).length,
							(imported.conflicts || []).length,
						]);
						frappe.msgprint({ title: __("Wialon Account Approved"), message, indicator: (imported.conflicts || []).length ? "orange" : "green" });
						frm.reload_doc();
					},
				})
			);
		}, __("Onboarding"));
	},
});

function show_duplicate_dialog(frm) {
	const merge_default = frm.doc.customer && frm.doc.customer !== frm.doc.suggested_existing_customer
		? frm.doc.customer
		: null;
	const dialog = new frappe.ui.Dialog({
		title: __("Resolve Duplicate Customer"),
		fields: [
			{ fieldname: "warning", fieldtype: "HTML", options: `<p class="text-muted">${__("Choose the Customer to keep. Optionally merge a duplicate Customer into it; all linked records will move to the kept Customer.")}</p>` },
			{ fieldname: "keep_customer", fieldtype: "Link", options: "Customer", label: __("Customer to Keep"), reqd: 1, default: frm.doc.suggested_existing_customer },
			{ fieldname: "merge_customer", fieldtype: "Link", options: "Customer", label: __("Duplicate Customer to Merge"), default: merge_default },
			{ fieldname: "activate", fieldtype: "Check", label: __("Activate Wialon Account After Resolution"), default: frm.doc.activation_status === "Activated" ? 0 : 1 },
		],
		primary_action_label: __("Resolve Duplicate"),
		primary_action(values) {
			frappe.confirm(
				values.merge_customer
					? __("Merge {0} into {1}? This moves linked records and removes the duplicate Customer.", [values.merge_customer, values.keep_customer])
					: __("Link this Wialon account to {0} without merging another Customer?", [values.keep_customer]),
				() => {
					dialog.hide();
					frappe.call({
						method: "omni_operations.telematics.sync.resolve_discovered_account_duplicate",
						args: { discovered_account_name: frm.doc.name, ...values },
						freeze: true,
						freeze_message: __("Resolving duplicate customer..."),
						callback() {
							frappe.show_alert({ message: __("Duplicate customer resolved"), indicator: "green" });
							frm.reload_doc();
						},
					});
				}
			);
		},
	});
	dialog.show();
}
