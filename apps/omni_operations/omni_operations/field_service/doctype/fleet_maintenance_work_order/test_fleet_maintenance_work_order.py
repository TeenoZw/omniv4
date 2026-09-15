import frappe
from frappe.tests.utils import FrappeTestCase


class TestFleetMaintenanceWorkOrder(FrappeTestCase):
	def test_vehicle_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "Fleet Maintenance Work Order",
				"customer": "Mapanje Hub",
				"company": "Mapanje Hub",
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)
