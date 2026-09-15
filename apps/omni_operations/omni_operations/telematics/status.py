import frappe


@frappe.whitelist()
def get_vehicle_telematics_status(vehicle):
	links = frappe.get_all(
		"Telematics Unit Link",
		filters={"vehicle": vehicle},
		fields=[
			"name",
			"provider_account",
			"provider",
			"status",
			"external_unit_id",
			"external_unit_name",
			"last_sync_datetime",
			"last_sync_status",
			"last_error",
			"sync_enabled",
		],
		order_by="modified desc",
	)

	if not links:
		return {
			"status": "Not Linked",
			"indicator": "gray",
			"message": "No telematics unit link",
			"links": [],
		}

	latest = links[0]
	if not latest.sync_enabled:
		return {
			"status": "Linked (Sync Off)",
			"indicator": "gray",
			"message": latest.external_unit_name or latest.external_unit_id,
			"links": links,
		}

	sync_status = latest.last_sync_status or "Never Synced"
	indicator = {
		"Success": "green",
		"Warning": "orange",
		"Failed": "red",
		"Never Synced": "gray",
	}.get(sync_status, "blue")

	return {
		"status": sync_status,
		"indicator": indicator,
		"message": latest.last_error or latest.external_unit_name or latest.external_unit_id,
		"links": links,
	}
