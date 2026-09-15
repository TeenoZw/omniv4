import frappe
from frappe.tests.utils import FrappeTestCase


class TestFleetDocument(FrappeTestCase):
	def test_requires_attachment_when_portal_visible(self):
		doc = frappe.get_doc(
			{
				"doctype": "Fleet Document",
				"title": "Portal Visible Test",
				"document_type": "Other",
				"status": "Active",
				"customer": "Mapanje Hub",
				"portal_visible": 1,
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)
