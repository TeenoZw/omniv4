import frappe
from frappe.model.document import Document


class TrackerProfile(Document):
	def validate(self):
		self.status = "Assigned" if self.current_vehicle else "In Stock"
		if self.current_vehicle and self.condition not in {"Brand New", "Used - Serviceable"}:
			frappe.throw("Return this tracker to inventory before marking it as unavailable for installation.")


@frappe.whitelist()
def get_assignment_context(tracker):
	tracker_doc = frappe.get_doc("Tracker Profile", tracker)
	tracker_doc.check_permission("read")

	from omni_operations.tracker_inventory.doctype.tracker_sim_assignment.tracker_sim_assignment import (
		get_active_tracker_sim_assignments,
	)

	assignments = get_active_tracker_sim_assignments(tracker=tracker)
	return {
		"tracker": tracker,
		"hub": tracker_doc.current_customer,
		"unit": tracker_doc.current_vehicle,
		"technician": tracker_doc.assigned_technician,
		"assignments": assignments,
		"sims": [row.sim for row in assignments if row.sim],
	}


@frappe.whitelist()
def assign_to_unit(tracker, vehicle, sim=None, technician=None):
	tracker_doc = frappe.get_doc("Tracker Profile", tracker)
	tracker_doc.check_permission("write")
	vehicle_doc = frappe.get_doc("Fleet Vehicle", vehicle)
	vehicle_doc.check_permission("read")
	if tracker_doc.condition not in {"Brand New", "Used - Serviceable"}:
		frappe.throw(
			f"Tracker {tracker} cannot be assigned while its condition is {tracker_doc.condition}. "
			"Inspect or repair it and set the condition to Used - Serviceable first."
		)

	if not vehicle_doc.customer:
		frappe.throw("Assign the unit to a customer hub before assigning a tracker.")

	from omni_operations.tracker_inventory.doctype.tracker_sim_assignment.tracker_sim_assignment import (
		get_active_tracker_sim_assignments,
	)

	active_assignments = get_active_tracker_sim_assignments(tracker=tracker)
	other_tracker = frappe.db.get_value(
		"Tracker SIM Assignment",
		{
			"vehicle": vehicle,
			"tracker": ["!=", tracker],
			"status": ["in", ["Assigned", "Installed"]],
		},
		["name", "tracker"],
		as_dict=True,
	)
	if other_tracker:
		frappe.throw(
			f"Unit {vehicle} is already assigned tracker {other_tracker.tracker} through "
			f"{other_tracker.name}. Remove that assignment before fitting another tracker."
		)
	active_sims = {row.sim for row in active_assignments if row.sim}
	if sim and active_sims and sim not in active_sims:
		frappe.throw(
			f"Tracker {tracker} is already paired with {', '.join(sorted(active_sims))}. "
			"Edit its SIM assignments before selecting a different SIM."
		)
	if not active_assignments and not sim:
		frappe.throw("Select a SIM for this tracker, or prepare its tracker/SIM pairing first.")

	updated_assignments = []
	for assignment in active_assignments:
		doc = frappe.get_doc("Tracker SIM Assignment", assignment.name)
		if doc.vehicle and doc.vehicle != vehicle:
			old_slot = doc.slot
			old_sim = doc.sim
			doc.status = "Removed"
			doc.save(ignore_permissions=True)
			doc = frappe.get_doc(
				{
					"doctype": "Tracker SIM Assignment",
					"status": "Assigned",
					"slot": old_slot,
					"tracker": tracker,
					"sim": old_sim,
				}
			)
		else:
			doc.status = "Installed" if doc.status == "Installed" else "Assigned"

		doc.customer = vehicle_doc.customer
		doc.vehicle = vehicle
		doc.assigned_technician = technician
		if doc.is_new():
			doc.insert(ignore_permissions=True)
		else:
			doc.save(ignore_permissions=True)
		updated_assignments.append(doc.name)

	if not active_assignments:
		doc = frappe.get_doc(
			{
				"doctype": "Tracker SIM Assignment",
				"status": "Assigned",
				"slot": "Primary",
				"tracker": tracker,
				"sim": sim,
				"customer": vehicle_doc.customer,
				"vehicle": vehicle,
				"assigned_technician": technician,
			}
		)
		doc.insert(ignore_permissions=True)
		updated_assignments.append(doc.name)

	_sync_telematics_links(tracker, vehicle, vehicle_doc.customer, sim or next(iter(active_sims), None))
	return {
		"tracker": tracker,
		"unit": vehicle,
		"hub": vehicle_doc.customer,
		"assignments": updated_assignments,
	}


@frappe.whitelist()
def return_to_inventory(tracker, condition="Used - Serviceable"):
	tracker_doc = frappe.get_doc("Tracker Profile", tracker)
	tracker_doc.check_permission("write")
	allowed_conditions = {"Brand New", "Used - Serviceable", "Needs Inspection", "Faulty", "Retired"}
	if condition not in allowed_conditions:
		frappe.throw("Select a valid tracker condition.")

	from omni_operations.tracker_inventory.doctype.tracker_sim_assignment.tracker_sim_assignment import (
		get_active_tracker_sim_assignments,
	)

	closed = []
	for assignment in get_active_tracker_sim_assignments(tracker=tracker):
		doc = frappe.get_doc("Tracker SIM Assignment", assignment.name)
		doc.status = "Removed"
		doc.save(ignore_permissions=True)
		closed.append(doc.name)

	frappe.db.set_value(
		"Tracker Profile",
		tracker,
		{
			"status": "In Stock",
			"condition": condition,
			"current_customer": None,
			"current_vehicle": None,
			"assigned_technician": None,
		},
		update_modified=True,
	)
	for link_name in frappe.get_all("Telematics Unit Link", filters={"tracker": tracker}, pluck="name"):
		frappe.db.set_value("Telematics Unit Link", link_name, {"tracker": None, "sim": None}, update_modified=False)

	return {"tracker": tracker, "status": "In Stock", "condition": condition, "closed_assignments": closed}


def _sync_telematics_links(tracker, vehicle, customer, sim=None):
	for link_name in frappe.get_all(
		"Telematics Unit Link",
		filters={"tracker": tracker, "vehicle": ["!=", vehicle]},
		pluck="name",
	):
		frappe.db.set_value("Telematics Unit Link", link_name, "tracker", None, update_modified=False)

	for link_name in frappe.get_all("Telematics Unit Link", filters={"vehicle": vehicle}, pluck="name"):
		values = {"tracker": tracker, "customer": customer}
		if sim:
			values["sim"] = sim
		frappe.db.set_value("Telematics Unit Link", link_name, values, update_modified=False)
