import frappe
from frappe.model.document import Document


class OmniLegalAcceptance(Document):
	def validate(self):
		if not self.accepted_terms or not self.accepted_privacy_policy:
			frappe.throw("Terms and Privacy Policy must both be accepted.")

