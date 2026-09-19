from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase

from omni_operations.omni_setup.customer_merge import get_merged_portal_users


class TestCustomerMerge(FrappeTestCase):
	@patch("omni_operations.omni_setup.customer_merge.frappe.get_all")
	def test_portal_users_are_deduplicated_before_merge(self, get_all):
		get_all.return_value = ["charlene@example.com", "charlene@example.com", "second@example.com"]

		users = get_merged_portal_users("Duplicate Customer", "Customer To Keep")

		self.assertEqual(users, ["charlene@example.com", "second@example.com"])
		get_all.assert_called_once_with(
			"Portal User",
			filters={"parent": ["in", ["Duplicate Customer", "Customer To Keep"]]},
			pluck="user",
		)
