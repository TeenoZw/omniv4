from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from omni_operations.omni_security.access import has_customer_permission, tracker_installation_query


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

	def test_technician_query_is_scoped_to_assigned_user(self):
		user = "assigned-technician@example.com"
		with patch("frappe.get_roles", return_value=["Technician"]):
			condition = tracker_installation_query(user)

		self.assertIn("`tabTracker Installation`.`technician`", condition)
		self.assertIn(user, condition)

	def test_technician_cannot_open_another_technicians_installation(self):
		doc = frappe._dict(doctype="Tracker Installation", technician="other@example.com")
		with patch("frappe.get_roles", return_value=["Technician"]):
			self.assertFalse(
				has_customer_permission(doc, user="assigned-technician@example.com", ptype="read")
			)
