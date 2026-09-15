import frappe
from frappe.tests.utils import FrappeTestCase


class TestCustomerFleetProfile(FrappeTestCase):
	def test_customer_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "Customer Fleet Profile",
				"company": "_Test Company",
				"status": "Active",
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)
