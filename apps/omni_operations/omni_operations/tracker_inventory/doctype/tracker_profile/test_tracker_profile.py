import frappe
from frappe.tests.utils import FrappeTestCase


class TestTrackerProfile(FrappeTestCase):
	def test_imei_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tracker Profile",
				"tracker_name": "Test Tracker",
				"item_code": "TRACKER-HW-4G",
				"status": "In Stock",
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_unassigned_tracker_is_in_stock(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tracker Profile",
				"imei": "TEST-IN-STOCK",
				"status": "Assigned",
				"condition": "Used - Serviceable",
			}
		)

		doc.validate()

		self.assertEqual(doc.status, "In Stock")
		self.assertEqual(doc.installation_stage, "In Inventory")

	def test_assigned_tracker_is_waiting_for_installation(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tracker Profile",
				"imei": "TEST-AWAITING-INSTALL",
				"current_vehicle": "TEST-UNIT",
				"condition": "Used - Serviceable",
			}
		)

		doc.validate()

		self.assertEqual(doc.status, "Assigned")
		self.assertEqual(doc.installation_stage, "Assigned - Awaiting Installation")

	def test_faulty_tracker_cannot_remain_assigned(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tracker Profile",
				"imei": "TEST-FAULTY-ASSIGNED",
				"current_vehicle": "TEST-UNIT",
				"condition": "Faulty",
			}
		)

		self.assertRaises(frappe.ValidationError, doc.validate)
