import frappe
from frappe.tests.utils import FrappeTestCase


class TestTelematicsProviderAccount(FrappeTestCase):
	def test_account_name_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "Telematics Provider Account",
				"provider": "Other",
				"company": "_Test Company",
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)
