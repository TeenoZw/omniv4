import frappe
from frappe.tests.utils import FrappeTestCase


class TestTrackerProfile(FrappeTestCase):
	def test_imei_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tracker Profile",
				"tracker_name": "Test Tracker",
				"item_code": "TRACKER-HW-4G",
				"status": "Available",
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)
