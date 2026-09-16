from frappe.model.document import Document


class OmniQuoteAddOn(Document):
	def validate(self):
		if self.status != "Available":
			self.is_enabled = 0
