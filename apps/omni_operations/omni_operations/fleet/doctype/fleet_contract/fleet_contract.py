import frappe
from frappe.model.document import Document
from frappe.utils import add_months, nowdate


class FleetContract(Document):
	def validate(self):
		if self.vehicle and not self.customer:
			self.customer = frappe.db.get_value("Fleet Vehicle", self.vehicle, "customer")

		if self.monthly_rate and not self.contract_value:
			self.contract_value = self.monthly_rate

		if not self.next_billing_date and self.start_date and self.status == "Active":
			self.next_billing_date = get_next_billing_date(self.start_date, self.billing_frequency)

		if self.end_date and self.end_date < nowdate() and self.status == "Active":
			self.status = "Expired"


def get_next_billing_date(start_date, billing_frequency):
	months = {
		"Monthly": 1,
		"Quarterly": 3,
		"Biannual": 6,
		"Annual": 12,
	}.get(billing_frequency, 1)
	return add_months(start_date, months)
