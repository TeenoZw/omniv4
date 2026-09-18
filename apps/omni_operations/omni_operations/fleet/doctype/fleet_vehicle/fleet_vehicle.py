import re

import frappe
from frappe.model.document import Document


class FleetVehicle(Document):
	def validate(self):
		if not self.company:
			from omni_operations.omni_setup.hub_companies import get_default_hub_company

			self.company = get_default_hub_company()


@frappe.whitelist()
def change_registration_number(vehicle, registration_number):
	if not frappe.db.exists("Fleet Vehicle", vehicle):
		frappe.throw(f"Vehicle {vehicle} does not exist.")
	vehicle_doc = frappe.get_doc("Fleet Vehicle", vehicle)
	if not vehicle_doc.has_permission("write"):
		frappe.throw("You do not have permission to change this vehicle registration.", frappe.PermissionError)

	registration_number = re.sub(r"\s+", " ", (registration_number or "").strip()).upper()
	if not registration_number:
		frappe.throw("Enter the vehicle registration number.")
	if registration_number != vehicle and frappe.db.exists("Fleet Vehicle", registration_number):
		frappe.throw(f"Vehicle {registration_number} already exists. Review that record instead of creating a duplicate.")

	new_name = vehicle
	if registration_number != vehicle:
		new_name = frappe.rename_doc(
			"Fleet Vehicle", vehicle, registration_number,
			force=True, ignore_permissions=True, show_alert=False,
		)
	frappe.db.set_value("Fleet Vehicle", new_name, "registration_number", registration_number)
	frappe.db.commit()
	return {"vehicle": new_name, "registration_number": registration_number}
