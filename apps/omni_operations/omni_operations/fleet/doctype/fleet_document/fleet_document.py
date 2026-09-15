import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class FleetDocument(Document):
	def validate(self):
		if self.vehicle and not self.customer:
			self.customer = frappe.db.get_value("Fleet Vehicle", self.vehicle, "customer")

		if self.expiry_date and self.expiry_date < nowdate() and self.status != "Expired":
			self.status = "Expired"

		if self.portal_visible and not self.attachment:
			frappe.throw("Attach a file before publishing this document to the customer portal.")
