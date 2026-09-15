import frappe
from frappe.tests.utils import FrappeTestCase


class TestTelematicsSyncLog(FrappeTestCase):
	def test_provider_account_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "Telematics Sync Log",
				"sync_type": "Unit Metadata",
				"status": "Success",
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)
