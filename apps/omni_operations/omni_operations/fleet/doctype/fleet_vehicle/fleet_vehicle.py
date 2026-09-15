from frappe.model.document import Document


class FleetVehicle(Document):
	def validate(self):
		if not self.company:
			from omni_operations.omni_setup.hub_companies import get_default_hub_company

			self.company = get_default_hub_company()
