import frappe


def get_notification_config():
	return {
		"for_doctype": {
			"Telematics Discovered Account": "omni_operations.notifications.get_duplicate_warnings",
		}
	}


def get_duplicate_warnings(as_list=False):
	filters = {
		"account_type": "Customer Hub",
		"duplicate_status": ["in", ["Possible Duplicate", "Multiple Matches"]],
	}
	if as_list:
		return frappe.get_list(
			"Telematics Discovered Account",
			filters=filters,
			fields=["name", "account_name", "duplicate_status", "duplicate_candidates"],
			order_by="last_seen desc",
		)
	return frappe.db.count("Telematics Discovered Account", filters=filters)
