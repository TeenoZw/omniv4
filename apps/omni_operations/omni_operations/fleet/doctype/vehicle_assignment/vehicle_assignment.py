import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class VehicleAssignment(Document):
	def validate(self):
		self.start_datetime = self.start_datetime or now_datetime()
		vehicle_customer = frappe.db.get_value("Fleet Vehicle", self.vehicle, "customer")
		if vehicle_customer and self.customer != vehicle_customer and self.status == "Active":
			self.notes = "\n".join(filter(None, [
				self.notes,
				f"Vehicle ownership changed from {vehicle_customer} to {self.customer} through this assignment.",
			]))

	def on_update(self):
		if self.status != "Active":
			return
		for assignment in frappe.get_all(
			"Vehicle Assignment",
			filters={"vehicle": self.vehicle, "status": "Active", "name": ["!=", self.name]},
			pluck="name",
		):
			frappe.db.set_value(
				"Vehicle Assignment", assignment,
				{"status": "Ended", "end_datetime": self.start_datetime}, update_modified=False,
			)
		frappe.db.set_value("Fleet Vehicle", self.vehicle, "customer", self.customer, update_modified=False)
