import frappe
from frappe.model.document import Document


class TelematicsDiscoveredAccount(Document):
	def validate(self):
		self.provider = frappe.db.get_value("Telematics Provider Account", self.provider_account, "provider")
		if self.activation_status == "Activated" and not self.customer:
			frappe.throw("An activated provider account must be linked to an Omni customer.")
		if self.activation_status == "Activated" and self.account_type != "Customer Hub":
			frappe.throw("Only customer hub accounts can be activated as Omni customers.")
		existing = frappe.db.exists(
			"Telematics Discovered Account",
			{"provider_account": self.provider_account, "external_account_id": self.external_account_id, "name": ["!=", self.name]},
		)
		if existing:
			frappe.throw(f"External account {self.external_account_id} is already recorded as {existing}.")
