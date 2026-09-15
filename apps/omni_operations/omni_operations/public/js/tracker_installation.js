frappe.ui.form.on("Tracker Installation", {
	setup(frm) {
		frm.set_query("vehicle", () => ({
			filters: frm.doc.customer ? { customer: frm.doc.customer } : {},
		}));
		frm.set_query("tracker", () => ({
			filters: { status: ["in", ["Available", "Prepared", "Reserved", "Assigned", "Installed"]] },
		}));
		frm.set_query("sim", () => ({
			filters: { status: ["in", ["Available", "Prepared", "Reserved", "Assigned", "Installed"]] },
		}));
	},

	refresh(frm) {
		render_installation_lifecycle(frm);

		if (frm.is_new()) {
			frm.dashboard.set_headline(__("Select customer, vehicle, tracker, SIM and technician, then save to begin the installation workflow."));
			return;
		}

		add_installation_actions(frm);
		add_installation_links(frm);
	},

	vehicle(frm) {
		if (!frm.doc.vehicle) {
			return;
		}

		frappe.db.get_value("Fleet Vehicle", frm.doc.vehicle, ["customer", "company"]).then((response) => {
			const values = response.message || {};
			if (values.customer && !frm.doc.customer) {
				frm.set_value("customer", values.customer);
			}
			if (values.company && !frm.doc.company) {
				frm.set_value("company", values.company);
			}
		});
	},
});

function render_installation_lifecycle(frm) {
	const lifecycle = [
		["Scheduled", __("Scheduled")],
		["In Progress", __("In Progress")],
		["Completed", __("Completed")],
	];
	const status = frm.doc.status || "Draft";
	const currentIndex = lifecycle.findIndex(([value]) => value === status);

	lifecycle.forEach(([value, label], index) => {
		const done = status === "Completed" || (currentIndex >= 0 && index <= currentIndex);
		frm.dashboard.add_indicator(label, done ? "green" : "gray");
	});

	[
		["customer", __("Customer")],
		["vehicle", __("Vehicle")],
		["tracker", __("Tracker")],
		["sim", __("SIM")],
		["technician", __("Technician")],
	].forEach(([fieldname, label]) => {
		frm.dashboard.add_indicator(label, frm.doc[fieldname] ? "blue" : "gray");
	});

	if (!frm.is_new()) {
		frm.dashboard.set_headline(get_installation_next_step(frm));
	}
}

function get_installation_next_step(frm) {
	if (!frm.doc.customer || !frm.doc.vehicle) {
		return __("Step 1: Confirm the customer hub and vehicle.");
	}
	if (!frm.doc.tracker || !frm.doc.sim) {
		return __("Step 2: Select the tracker and SIM kit from inventory.");
	}
	if (!frm.doc.technician) {
		return __("Step 3: Assign the technician and scheduled date.");
	}
	if (frm.doc.status === "Scheduled") {
		return __("Step 4: Start work when the technician begins the installation.");
	}
	if (frm.doc.status === "In Progress") {
		return __("Step 5: Capture work performed, signoff and completion details.");
	}
	if (frm.doc.status === "Completed") {
		return __("Installation completed. Confirm telematics link, billing and portal visibility.");
	}
	return __("Follow the installation lifecycle from scheduled work to completed installation.");
}

function add_installation_actions(frm) {
	if (frm.doc.status === "Scheduled") {
		frm.add_custom_button(__("Start Work"), () => {
			frm.set_value("status", "In Progress");
			frm.save();
		}, __("Workflow"));
	}

	if (["Scheduled", "In Progress"].includes(frm.doc.status)) {
		frm.add_custom_button(__("Complete Installation"), () => {
			frm.set_value("status", "Completed");
			if (!frm.doc.completed_date) {
				frm.set_value("completed_date", frappe.datetime.now_datetime());
			}
			frm.save();
		}, __("Workflow"));
	}

	if (!["Completed", "Cancelled", "Failed"].includes(frm.doc.status)) {
		frm.add_custom_button(__("Mark Failed"), () => {
			frm.set_value("status", "Failed");
			frm.save();
		}, __("Workflow"));
	}
}

function add_installation_links(frm) {
	frm.add_custom_button(__("Customer Fleet"), () => {
		frappe.set_route("List", "Customer Fleet Profile", { customer: frm.doc.customer });
	}, __("View"));

	frm.add_custom_button(__("Vehicle"), () => {
		if (frm.doc.vehicle) {
			frappe.set_route("Form", "Fleet Vehicle", frm.doc.vehicle);
		}
	}, __("View"));

	frm.add_custom_button(__("SIM Assignment"), () => {
		frappe.set_route("List", "Tracker SIM Assignment", { source_installation: frm.doc.name });
	}, __("View"));

	frm.add_custom_button(__("Telematics Links"), () => {
		frappe.set_route("List", "Telematics Unit Link", { vehicle: frm.doc.vehicle });
	}, __("View"));
}
