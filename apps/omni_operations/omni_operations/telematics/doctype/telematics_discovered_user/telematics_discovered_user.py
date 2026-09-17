import frappe
from frappe.model.document import Document


class TelematicsDiscoveredUser(Document):
	def validate(self):
		self.provider = frappe.db.get_value(
			"Telematics Provider Account", self.provider_account, "provider"
		)
		if self.customer and self.review_status == "Needs Review":
			self.review_status = "Mapped to Customer"
		if self.review_status == "Mapped to Customer" and not self.customer:
			frappe.throw("Select the Omni customer or hub before marking this provider user as mapped.")
		self.validate_unique_external_user()

	def validate_unique_external_user(self):
		if not self.provider_account or not self.external_user_id:
			return

		existing = frappe.db.exists(
			"Telematics Discovered User",
			{
				"provider_account": self.provider_account,
				"external_user_id": self.external_user_id,
				"name": ["!=", self.name],
			},
		)
		if existing:
			frappe.throw(f"External user {self.external_user_id} is already recorded as {existing}.")
