import frappe

from omni_operations.telematics.sync import sync_provider_units


def sync_enabled_provider_accounts():
	"""Sync active provider accounts that have automatic sync enabled."""
	provider_accounts = frappe.get_all(
		"Telematics Provider Account",
		filters={
			"status": "Active",
			"sync_enabled": 1,
		},
		pluck="name",
	)
	results = []

	for provider_account in provider_accounts:
		try:
			results.append(sync_provider_units(provider_account))
		except Exception:
			frappe.log_error(
				title=f"Telematics auto sync failed for {provider_account}",
				message=frappe.get_traceback(),
			)

	return results
