import frappe
from frappe.model.document import Document


class TelematicsProviderAccount(Document):
	def validate(self):
		self.set_default_scope()
		self.validate_scope()
		self.validate_parent()

	def set_default_scope(self):
		if not self.account_scope:
			self.account_scope = "Customer Hub" if self.customer else "System-wide"

	def validate_scope(self):
		if self.account_scope == "Customer Hub" and not self.customer:
			frappe.throw("Customer is required when Account Scope is Customer Hub.")

		if self.account_scope in ("System-wide", "Regional Admin"):
			self.customer = None

	def validate_parent(self):
		if self.parent_provider_account and self.parent_provider_account == self.name:
			frappe.throw("Parent Provider Account cannot be the same account.")
