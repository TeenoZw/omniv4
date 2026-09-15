import frappe
from frappe.tests.utils import FrappeTestCase


class TestSIMProfile(FrappeTestCase):
	def test_iccid_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "SIM Profile",
				"item_code": "SIM-IOT",
				"status": "Available",
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)
