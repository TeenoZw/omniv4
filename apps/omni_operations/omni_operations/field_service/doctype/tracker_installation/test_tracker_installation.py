import frappe
from frappe.tests.utils import FrappeTestCase


class TestTrackerInstallation(FrappeTestCase):
	def test_vehicle_is_required(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tracker Installation",
				"customer": "Test Customer",
				"company": "_Test Company",
				"tracker": "867530900001111",
				"status": "Scheduled",
			}
		)

		self.assertRaises(frappe.MandatoryError, doc.insert)

	def test_completion_requires_field_evidence(self):
		doc = frappe.get_doc({"doctype": "Tracker Installation", "status": "Completed"})
		with self.assertRaises(frappe.ValidationError):
			doc._validate_completion()

	def test_completion_accepts_photo_evidence(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tracker Installation",
				"status": "Completed",
				"technician": "Administrator",
				"scheduled_date": "2026-10-19 08:00:00",
				"completed_date": "2026-10-19 09:00:00",
				"installation_location": "Customer yard",
				"work_performed": "Installed tracker and confirmed telemetry.",
				"customer_signoff_name": "Customer Representative",
				"installation_photo": "/files/installation-smoke.jpg",
			}
		)
		doc._validate_completion()
