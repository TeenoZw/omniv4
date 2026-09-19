from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase

from omni_operations.fleet.customer_360 import get_customer_for_user


class TestCustomerForUser(FrappeTestCase):
	@patch("omni_operations.fleet.customer_360.frappe.get_all")
	@patch("omni_operations.fleet.customer_360.frappe.db.exists")
	@patch("omni_operations.fleet.customer_360.frappe.db.get_value")
	def test_ignores_stale_customer_links_after_merge(self, get_value, exists, get_all):
		get_value.return_value = "charlenemazuru@gmail.com"
		get_all.return_value = ["Charlene M", "Mazuru Hub", "Mazuru Hub"]
		exists.side_effect = lambda doctype, name: doctype == "Customer" and name == "Mazuru Hub"

		self.assertEqual(get_customer_for_user("charlenemazuru@gmail.com"), "Mazuru Hub")

	@patch("omni_operations.fleet.customer_360.frappe.get_all")
	@patch("omni_operations.fleet.customer_360.frappe.db.exists", return_value=True)
	@patch("omni_operations.fleet.customer_360.frappe.db.get_value", return_value="shared@example.com")
	def test_rejects_multiple_existing_customer_links(self, _get_value, _exists, get_all):
		get_all.return_value = ["Customer A", "Customer B"]

		self.assertIsNone(get_customer_for_user("shared@example.com"))
