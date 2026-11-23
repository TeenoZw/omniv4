frappe.ui.form.on("Tracker SIM Assignment", {
	setup(frm) {
		frm.set_query("vehicle", () => ({
			filters: frm.doc.customer ? { customer: frm.doc.customer } : {},
		}));
		frm.set_query("tracker", () => ({
			filters: {
				status: ["in", ["In Stock", "Assigned"]],
				condition: ["in", ["Brand New", "Used - Serviceable"]],
			},
		}));
		frm.set_query("sim", () => ({
			filters: { status: ["in", ["Available", "Prepared", "Reserved", "Assigned", "Installed"]] },
		}));
	},

	refresh(frm) {
		frm.set_df_property("status", "read_only", 1);
		render_assignment_lifecycle(frm);

		if (frm.is_new()) {
			frm.dashboard.set_headline(__("Pick a tracker and SIM first. Customer and vehicle can be added later when the kit is reserved or assigned."));
			return;
		}

		add_assignment_actions(frm);
		add_assignment_links(frm);
	},

	vehicle(frm) {
		if (!frm.doc.vehicle) {
			return;
		}

		frappe.db.get_value("Fleet Vehicle", frm.doc.vehicle, "customer").then((response) => {
			if (response.message && response.message.customer && !frm.doc.customer) {
				frm.set_value("customer", response.message.customer);
			}
		});
	},
});

function render_assignment_lifecycle(frm) {
	const statuses = ["Prepared", "Reserved", "Assigned", "Installed"];
	const status = frm.doc.status || "Prepared";
	const currentIndex = statuses.indexOf(status);

	statuses.forEach((value, index) => {
		const isDone = currentIndex >= 0 && index <= currentIndex;
		frm.dashboard.add_indicator(__(value), isDone ? "green" : "gray");
	});

	if (["Removed", "Cancelled"].includes(status)) {
		frm.dashboard.add_indicator(__(status), "gray");
	}

	[
		["tracker", __("Tracker")],
		["sim", __("SIM")],
		["customer", __("Customer")],
		["vehicle", __("Vehicle")],
	].forEach(([fieldname, label]) => {
		frm.dashboard.add_indicator(label, frm.doc[fieldname] ? "blue" : "gray");
	});

	if (!frm.is_new()) {
		frm.dashboard.set_headline(get_assignment_next_step(frm));
	}
}

function get_assignment_next_step(frm) {
	if (!frm.doc.tracker || !frm.doc.sim) {
		return __("Step 1: Pair the tracker hardware with a SIM.");
	}
	if (frm.doc.status === "Prepared") {
		return __("Prepared kit: keep it in inventory or reserve it for a customer when onboarding starts.");
	}
	if (frm.doc.status === "Reserved") {
		return __("Reserved kit: choose the customer, vehicle and technician before installation.");
	}
	if (frm.doc.status === "Assigned") {
		return __("Assigned only: this kit is linked to the vehicle but is not yet installed. Open and complete the installation job after the physical work, evidence and customer sign-off are captured.");
	}
	if (frm.doc.status === "Installed") {
		return __("Installed: the linked installation job was completed with installation details, evidence and customer sign-off.");
	}
	return __("Assignment closed. Create a new assignment if this kit is reused.");
}

function add_assignment_actions(frm) {
	const transitions = {
		Prepared: ["Reserved", "Assigned"],
		Reserved: ["Assigned", "Cancelled"],
		Assigned: ["Removed"],
		Installed: ["Removed"],
	};

	(transitions[frm.doc.status] || []).forEach((status) => {
		frm.add_custom_button(__(`Mark ${status}`), () => {
			frm.set_value("status", status);
			frm.save();
		}, __("Workflow"));
	});

	if (frm.doc.status === "Assigned") {
		frm.add_custom_button(__("Open Installation Job"), () => {
			if (frm.doc.source_installation) {
				frappe.set_route("Form", "Tracker Installation", frm.doc.source_installation);
				return;
			}
			frappe.new_doc("Tracker Installation", {
				customer: frm.doc.customer,
				company: frappe.defaults.get_default("Company"),
				vehicle: frm.doc.vehicle,
				tracker: frm.doc.tracker,
				sim: frm.doc.sim,
				technician: frm.doc.assigned_technician,
				status: "Scheduled",
			});
		}, __("Workflow"));
	}
}

function add_assignment_links(frm) {
	frm.add_custom_button(__("Tracker"), () => {
		if (frm.doc.tracker) {
			frappe.set_route("Form", "Tracker Profile", frm.doc.tracker);
		}
	}, __("View"));

	frm.add_custom_button(__("SIM"), () => {
		if (frm.doc.sim) {
			frappe.set_route("Form", "SIM Profile", frm.doc.sim);
		}
	}, __("View"));

	frm.add_custom_button(__("Vehicle"), () => {
		if (frm.doc.vehicle) {
			frappe.set_route("Form", "Fleet Vehicle", frm.doc.vehicle);
		}
	}, __("View"));

	if (frm.doc.source_installation) {
		frm.add_custom_button(__("Installation Job"), () => {
			frappe.set_route("Form", "Tracker Installation", frm.doc.source_installation);
		}, __("View"));
	}
}
