import frappe
from frappe.tests.utils import FrappeTestCase


class TestVehicleAssignment(FrappeTestCase):
	def test_vehicle_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "Vehicle Assignment",
				"driver": "FD-2026-0001",
				"company": "_Test Company",
				"status": "Active",
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)
