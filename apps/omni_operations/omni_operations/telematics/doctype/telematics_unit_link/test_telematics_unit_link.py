import frappe
from frappe.tests.utils import FrappeTestCase


class TestTelematicsUnitLink(FrappeTestCase):
	def test_provider_account_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "Telematics Unit Link",
				"vehicle": "ADE-1001",
				"external_unit_id": "unit-1",
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)
