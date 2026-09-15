from frappe.model.document import Document


class CustomerFleetProfile(Document):
	def refresh_commercial_summary(self):
		from omni_operations.omni_setup.commercial import get_customer_commercial_summary

		summary = get_customer_commercial_summary(self.customer, self.company)
		self.update(summary)
