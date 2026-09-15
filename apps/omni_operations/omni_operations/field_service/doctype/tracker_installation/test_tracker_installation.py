import frappe
from frappe.tests.utils import FrappeTestCase


class TestTrackerInstallation(FrappeTestCase):
	def test_vehicle_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tracker Installation",
				"customer": "Test Customer",
				"company": "_Test Company",
				"tracker": "867530900001111",
				"status": "Scheduled",
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)
