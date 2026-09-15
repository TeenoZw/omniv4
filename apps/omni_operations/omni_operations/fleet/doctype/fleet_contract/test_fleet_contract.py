import frappe
from frappe.tests.utils import FrappeTestCase


class TestFleetContract(FrappeTestCase):
	def test_customer_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "Fleet Contract",
				"contract_title": "Missing Customer Test",
				"company": "Mapanje Hub",
				"service_item": "FLEET-MONTHLY-SERVICE",
				"start_date": "2026-08-18",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert)
