from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestTrackerSIMAssignment(FrappeTestCase):
	def test_installed_requires_source_installation(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tracker SIM Assignment",
				"status": "Installed",
				"customer": "Test Customer",
				"vehicle": "TEST-VEHICLE",
			}
		)

		with self.assertRaises(frappe.ValidationError):
			doc._validate_installed_source()

	def test_installed_requires_completed_source_installation(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tracker SIM Assignment",
				"status": "Installed",
				"source_installation": "TI-TEST-0001",
			}
		)

		with patch("frappe.db.get_value", return_value="In Progress"):
			with self.assertRaises(frappe.ValidationError):
				doc._validate_installed_source()

	def test_completed_source_installation_can_mark_kit_installed(self):
		doc = frappe.get_doc(
			{
				"doctype": "Tracker SIM Assignment",
				"status": "Installed",
				"source_installation": "TI-TEST-0001",
			}
		)

		with patch("frappe.db.get_value", return_value="Completed"):
			doc._validate_installed_source()
