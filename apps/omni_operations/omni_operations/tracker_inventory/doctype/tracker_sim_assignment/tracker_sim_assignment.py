import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


ACTIVE_STATUSES = {"Prepared", "Reserved", "Assigned", "Installed"}
END_STATUSES = {"Removed", "Cancelled"}
STATUS_PRIORITY = {
	"Installed": 4,
	"Assigned": 3,
	"Reserved": 2,
	"Prepared": 1,
}


class TrackerSIMAssignment(Document):
	def validate(self):
		self._set_default_dates()
		self._validate_context()
		if self.status in ACTIVE_STATUSES:
			self._validate_unique_active_sim()
			self._validate_unique_active_tracker_slot()

	def on_update(self):
		sync_tracker_sim_assignment_state(self.tracker)
		sync_sim_assignment_state(self.sim)

	def on_trash(self):
		tracker = self.tracker
		sim = self.sim
		self.tracker = None
		self.sim = None
		if tracker:
			sync_tracker_sim_assignment_state(tracker, exclude_assignment=self.name)
		if sim:
			sync_sim_assignment_state(sim, exclude_assignment=self.name)

	def _set_default_dates(self):
		current_time = now_datetime()
		if self.status == "Prepared" and not self.prepared_date:
			self.prepared_date = current_time
		if self.status == "Assigned" and not self.assigned_date:
			self.assigned_date = current_time
		if self.status == "Installed" and not self.installed_date:
			self.installed_date = current_time
		if self.status in END_STATUSES and not self.removed_date:
			self.removed_date = current_time

	def _validate_context(self):
		if self.vehicle:
			vehicle_customer = frappe.db.get_value("Fleet Vehicle", self.vehicle, "customer")
			if not vehicle_customer:
				frappe.throw("Selected vehicle does not exist.")
			if self.customer and vehicle_customer != self.customer:
				frappe.throw("The selected vehicle belongs to a different customer.")
			if not self.customer:
				self.customer = vehicle_customer

		if self.status in {"Assigned", "Installed"} and (not self.customer or not self.vehicle):
			frappe.throw("Customer and vehicle are required when a SIM assignment is assigned or installed.")

		if self.status == "Installed" and not self.vehicle:
			frappe.throw("Vehicle is required when a SIM assignment is installed.")

	def _validate_unique_active_sim(self):
		filters = {
			"sim": self.sim,
			"status": ["in", list(ACTIVE_STATUSES)],
		}
		if self.name:
			filters["name"] = ["!=", self.name]
		existing = frappe.db.get_value("Tracker SIM Assignment", filters, "name")
		if existing:
			frappe.throw(f"SIM {self.sim} already has an active assignment: {existing}.")

	def _validate_unique_active_tracker_slot(self):
		filters = {
			"tracker": self.tracker,
			"slot": self.slot,
			"status": ["in", list(ACTIVE_STATUSES)],
		}
		if self.name:
			filters["name"] = ["!=", self.name]
		existing = frappe.db.get_value("Tracker SIM Assignment", filters, "name")
		if existing:
			frappe.throw(f"Tracker {self.tracker} already has an active {self.slot} SIM assignment: {existing}.")


def get_active_tracker_sim_assignments(tracker=None, sim=None, exclude_assignment=None):
	filters = {"status": ["in", list(ACTIVE_STATUSES)]}
	if tracker:
		filters["tracker"] = tracker
	if sim:
		filters["sim"] = sim
	if exclude_assignment:
		filters["name"] = ["!=", exclude_assignment]

	assignments = frappe.get_all(
		"Tracker SIM Assignment",
		filters=filters,
		fields=[
			"name",
			"status",
			"slot",
			"tracker",
			"sim",
			"customer",
			"vehicle",
			"assigned_technician",
			"prepared_date",
			"assigned_date",
			"installed_date",
			"modified",
		],
		order_by="modified desc",
	)
	return sorted(assignments, key=lambda row: STATUS_PRIORITY.get(row.status, 0), reverse=True)


def sync_tracker_sim_assignment_state(tracker, exclude_assignment=None):
	if not tracker or not frappe.db.exists("Tracker Profile", tracker):
		return

	assignments = get_active_tracker_sim_assignments(tracker=tracker, exclude_assignment=exclude_assignment)
	if not assignments:
		frappe.db.set_value(
			"Tracker Profile",
			tracker,
			{
				"status": "Available",
				"current_customer": None,
				"current_vehicle": None,
				"assigned_technician": None,
			},
			update_modified=False,
		)
		return

	primary = assignments[0]
	status = "Prepared" if primary.status == "Prepared" else primary.status
	update = {
		"status": status,
		"current_customer": primary.customer,
		"current_vehicle": primary.vehicle,
		"assigned_technician": primary.assigned_technician,
	}
	if primary.status == "Installed" and primary.installed_date:
		update["last_installation_date"] = primary.installed_date.date()

	frappe.db.set_value("Tracker Profile", tracker, update, update_modified=False)


def sync_sim_assignment_state(sim, exclude_assignment=None):
	if not sim or not frappe.db.exists("SIM Profile", sim):
		return

	assignments = get_active_tracker_sim_assignments(sim=sim, exclude_assignment=exclude_assignment)
	if not assignments:
		frappe.db.set_value(
			"SIM Profile",
			sim,
			{
				"status": "Available",
				"current_customer": None,
				"current_vehicle": None,
				"current_tracker": None,
			},
			update_modified=False,
		)
		return

	primary = assignments[0]
	status = primary.status
	frappe.db.set_value(
		"SIM Profile",
		sim,
		{
			"status": status,
			"current_customer": primary.customer,
			"current_vehicle": primary.vehicle,
			"current_tracker": primary.tracker,
		},
		update_modified=False,
	)


def upsert_assignment_from_installation(installation):
	if not installation.sim:
		return None

	status_map = {
		"Draft": "Reserved",
		"Scheduled": "Assigned",
		"In Progress": "Assigned",
		"Completed": "Installed",
		"Cancelled": "Cancelled",
		"Failed": "Removed",
	}
	status = status_map.get(installation.status, "Assigned")
	existing = frappe.db.get_value(
		"Tracker SIM Assignment",
		{"source_installation": installation.name, "sim": installation.sim},
		"name",
	)
	if not existing:
		existing = frappe.db.get_value(
			"Tracker SIM Assignment",
			{
				"sim": installation.sim,
				"status": ["in", list(ACTIVE_STATUSES)],
			},
			"name",
		)

	if existing:
		doc = frappe.get_doc("Tracker SIM Assignment", existing)
		if doc.tracker and doc.tracker != installation.tracker:
			frappe.throw(
				f"SIM {installation.sim} is already paired to tracker {doc.tracker}. "
				f"Remove that assignment before installing it on tracker {installation.tracker}."
			)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Tracker SIM Assignment",
				"naming_series": "TSA-.YYYY.-.####",
				"source_installation": installation.name,
				"sim": installation.sim,
			}
		)

	doc.status = status
	doc.slot = doc.slot or "Primary"
	doc.tracker = installation.tracker
	doc.customer = installation.customer
	doc.vehicle = installation.vehicle
	doc.assigned_technician = installation.technician
	if status == "Installed":
		doc.installed_date = installation.completed_date or now_datetime()
	elif status == "Assigned":
		doc.assigned_date = installation.scheduled_date or now_datetime()
	elif status == "Reserved":
		doc.prepared_date = installation.scheduled_date or now_datetime()
	doc.notes = f"Managed from Tracker Installation {installation.name}."

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	return doc.name


@frappe.whitelist()
def sync_all_tracker_sim_assignment_state():
	trackers = set()
	sims = set()
	for assignment in frappe.get_all(
		"Tracker SIM Assignment",
		fields=["tracker", "sim"],
		limit=5000,
	):
		if assignment.tracker:
			trackers.add(assignment.tracker)
		if assignment.sim:
			sims.add(assignment.sim)

	for tracker in trackers:
		sync_tracker_sim_assignment_state(tracker)
	for sim in sims:
		sync_sim_assignment_state(sim)

	frappe.db.commit()
	return {"trackers": len(trackers), "sims": len(sims)}
