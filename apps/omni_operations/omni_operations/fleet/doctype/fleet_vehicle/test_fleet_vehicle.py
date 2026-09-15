import frappe
from frappe.tests.utils import FrappeTestCase


class TestFleetVehicle(FrappeTestCase):
	def test_registration_number_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "Fleet Vehicle",
				"customer": "Test Customer",
				"company": "_Test Company",
				"vehicle_type": "Car",
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)
