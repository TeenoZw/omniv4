frappe.ui.form.on("Tracker Profile", {
	refresh(frm) {
		render_inventory_lifecycle(frm, "tracker");

		if (frm.is_new()) {
			return;
		}

		frm.add_custom_button(__("SIM Assignments"), () => {
			frappe.set_route("List", "Tracker SIM Assignment", { tracker: frm.doc.name });
		}, __("View"));

		frm.add_custom_button(__("New SIM Assignment"), () => {
			frappe.new_doc("Tracker SIM Assignment", {
				tracker: frm.doc.name,
				customer: frm.doc.current_customer,
				vehicle: frm.doc.current_vehicle,
				assigned_technician: frm.doc.assigned_technician,
			});
		}, __("Workflow"));

		if (frm.doc.current_vehicle) {
			frm.add_custom_button(__("Current Vehicle"), () => {
				frappe.set_route("Form", "Fleet Vehicle", frm.doc.current_vehicle);
			}, __("View"));
		}
	},
});

function render_inventory_lifecycle(frm, kind) {
	const statuses = ["Available", "Prepared", "Reserved", "Assigned", "Installed"];
	const status = frm.doc.status || "Available";
	const currentIndex = statuses.indexOf(status);

	statuses.forEach((value, index) => {
		const isDone = currentIndex >= 0 && index <= currentIndex;
		frm.dashboard.add_indicator(__(value), isDone ? "green" : "gray");
	});

	if (["Faulty", "Returned", "Retired", "Suspended", "Lost"].includes(status)) {
		frm.dashboard.add_indicator(__(status), "orange");
	}

	const identifier = kind === "tracker" ? frm.doc.imei : frm.doc.iccid;
	const assignedTo = frm.doc.current_vehicle || frm.doc.current_customer || __("No customer assignment");
	frm.dashboard.set_headline(
		`${frappe.utils.escape_html(identifier || frm.doc.name)}: ` +
			`<b>${frappe.utils.escape_html(status)}</b><br>` +
			`${__("Current")}: ${frappe.utils.escape_html(assignedTo)}`
	);
}
