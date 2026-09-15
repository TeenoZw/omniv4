import frappe
from frappe.tests.utils import FrappeTestCase


class TestFleetDriver(FrappeTestCase):
	def test_driver_name_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "Fleet Driver",
				"company": "_Test Company",
				"status": "Active",
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)
