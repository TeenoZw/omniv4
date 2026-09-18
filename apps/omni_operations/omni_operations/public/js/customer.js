frappe.ui.form.on("Customer", {
	refresh(frm) {
		const can_merge = frappe.user.has_role("System Manager") || frappe.user.has_role("Omni Operations Admin");
		if (frm.is_new() || !can_merge) return;

		frm.add_custom_button(__("Merge Into Another Customer"), () => {
			const dialog = new frappe.ui.Dialog({
				title: __("Merge Customer"),
				fields: [
					{
						fieldname: "warning",
						fieldtype: "HTML",
						options: `<p>${__("All records linked to <b>{0}</b> will move to the customer selected below. <b>{0}</b> will then be removed. This cannot be undone.", [frappe.utils.escape_html(frm.doc.name)])}</p>`,
					},
					{
						fieldname: "target_customer",
						fieldtype: "Link",
						options: "Customer",
						label: __("Customer to Keep"),
						reqd: 1,
						get_query: () => ({ filters: [["Customer", "name", "!=", frm.doc.name]] }),
					},
				],
				primary_action_label: __("Merge Customer"),
				primary_action(values) {
					frappe.confirm(
						__("Permanently merge {0} into {1}?", [frm.doc.name, values.target_customer]),
						() => {
							dialog.hide();
							frappe.call({
								method: "omni_operations.omni_setup.customer_merge.merge_customer",
								args: { source_customer: frm.doc.name, target_customer: values.target_customer },
								freeze: true,
								freeze_message: __("Merging customer records..."),
								callback(response) {
									const result = response.message || {};
									frappe.show_alert({ message: __("Merged into {0}", [result.customer]), indicator: "green" });
									frappe.set_route("Form", "Customer", result.customer);
								},
							});
						}
					);
				},
			});
			dialog.show();
		}, __("Actions"));
	},
});
