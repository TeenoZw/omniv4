import frappe

from omni_operations.telematics.sync import discover_provider_accounts, discover_provider_users, sync_provider_units


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
			results.append(
				{
					"provider_account": provider_account,
					"accounts": discover_provider_accounts(provider_account),
					"users": discover_provider_users(provider_account),
					"units": sync_provider_units(provider_account),
				}
			)
		except Exception:
			frappe.log_error(
				title=f"Telematics auto sync failed for {provider_account}",
				message=frappe.get_traceback(),
			)

	return results
