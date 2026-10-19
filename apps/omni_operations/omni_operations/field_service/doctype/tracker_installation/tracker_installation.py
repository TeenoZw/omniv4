from frappe.model.document import Document


class TrackerInstallation(Document):
	def validate(self):
		if self.vehicle and self.customer:
			self._validate_vehicle_customer()
		self._validate_status_transition()
		self._validate_completion()

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

	def _validate_status_transition(self):
		import frappe

		if self.is_new() or self.status != "Completed":
			return
		previous = self.get_doc_before_save()
		if previous and previous.status not in {"In Progress", "Completed"}:
			frappe.throw("Start the installation before marking it completed.")

	def _validate_completion(self):
		import frappe

		if self.status != "Completed" or (not self.is_new() and not self.has_value_changed("status")):
			return
		required = {
			"technician": "Technician",
			"scheduled_date": "Scheduled Date",
			"completed_date": "Completed Date",
			"installation_location": "Installation Location",
			"work_performed": "Work Performed",
			"customer_signoff_name": "Customer Signoff Name",
		}
		missing = [label for fieldname, label in required.items() if not self.get(fieldname)]
		if missing:
			frappe.throw(f"Complete these installation fields first: {', '.join(missing)}.")
		if not self.installation_photo and not self.completion_evidence:
			frappe.throw("Attach an installation photo or completion evidence before completing the job.")
