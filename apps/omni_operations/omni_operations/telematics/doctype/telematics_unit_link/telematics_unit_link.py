import frappe
from frappe.model.document import Document


class TelematicsUnitLink(Document):
	def validate(self):
		self.set_provider_from_account()
		self.set_customer_from_vehicle()
		self.validate_unique_external_unit()

	def set_provider_from_account(self):
		if self.provider_account:
			self.provider = frappe.db.get_value("Telematics Provider Account", self.provider_account, "provider")

	def set_customer_from_vehicle(self):
		if self.vehicle and not self.customer:
			self.customer = frappe.db.get_value("Fleet Vehicle", self.vehicle, "customer")

	def validate_unique_external_unit(self):
		if not self.provider_account or not self.external_unit_id:
			return

		existing_link = frappe.db.exists(
			"Telematics Unit Link",
			{
				"provider_account": self.provider_account,
				"external_unit_id": self.external_unit_id,
				"name": ["!=", self.name],
			},
		)
		if existing_link:
			frappe.throw(
				f"External Unit ID {self.external_unit_id} is already linked to {existing_link} for this provider account."
			)
