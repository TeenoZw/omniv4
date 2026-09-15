from frappe.model.document import Document


class TrackerInstallation(Document):
	def validate(self):
		if self.vehicle and self.customer:
			self._validate_vehicle_customer()

	def on_update(self):
		if self.tracker and self.sim:
			from omni_operations.tracker_inventory.doctype.tracker_sim_assignment.tracker_sim_assignment import (
				upsert_assignment_from_installation,
			)

			upsert_assignment_from_installation(self)

	def _validate_vehicle_customer(self):
		import frappe

		vehicle_customer = frappe.db.get_value("Fleet Vehicle", self.vehicle, "customer")
		if vehicle_customer and vehicle_customer != self.customer:
			frappe.throw("The selected vehicle belongs to a different customer.")
