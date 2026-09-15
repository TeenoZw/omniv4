frappe.ui.form.on("SIM Profile", {
	refresh(frm) {
		render_sim_lifecycle(frm);

		if (frm.is_new()) {
			return;
		}

		frm.add_custom_button(__("SIM Assignments"), () => {
			frappe.set_route("List", "Tracker SIM Assignment", { sim: frm.doc.name });
		}, __("View"));

		frm.add_custom_button(__("New Tracker Pairing"), () => {
			frappe.new_doc("Tracker SIM Assignment", {
				sim: frm.doc.name,
				customer: frm.doc.current_customer,
				vehicle: frm.doc.current_vehicle,
			});
		}, __("Workflow"));

		if (frm.doc.current_tracker) {
			frm.add_custom_button(__("Current Tracker"), () => {
				frappe.set_route("Form", "Tracker Profile", frm.doc.current_tracker);
			}, __("View"));
		}
	},
});

function render_sim_lifecycle(frm) {
	const statuses = ["Available", "Prepared", "Reserved", "Assigned", "Installed"];
	const status = frm.doc.status || "Available";
	const currentIndex = statuses.indexOf(status);

	statuses.forEach((value, index) => {
		const isDone = currentIndex >= 0 && index <= currentIndex;
		frm.dashboard.add_indicator(__(value), isDone ? "green" : "gray");
	});

	if (["Suspended", "Lost", "Retired"].includes(status)) {
		frm.dashboard.add_indicator(__(status), "orange");
	}

	const assignedTo = frm.doc.current_vehicle || frm.doc.current_tracker || frm.doc.current_customer || __("No kit/customer assignment");
	frm.dashboard.set_headline(
		`${frappe.utils.escape_html(frm.doc.iccid || frm.doc.name)}: ` +
			`<b>${frappe.utils.escape_html(status)}</b><br>` +
			`${__("Current")}: ${frappe.utils.escape_html(assignedTo)}`
	);
}
