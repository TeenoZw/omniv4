import frappe

from omni_operations.omni_setup.commercial import get_default_company


def ensure_imported_fleet_provider_account():
	account_name = "Imported Fleet Telematics Staging"
	if frappe.db.exists("Telematics Provider Account", account_name):
		return account_name

	doc = frappe.get_doc(
		{
			"doctype": "Telematics Provider Account",
			"account_name": account_name,
			"provider": "Other",
			"status": "Testing",
			"company": get_default_company(),
			"auth_type": "None",
			"sync_enabled": 0,
			"last_sync_status": "Never Synced",
			"notes": "Migration staging account. Replace with a real provider account before live sync.",
		}
	).insert(ignore_permissions=True)
	return doc.name


def latest_installation_for_vehicle(vehicle, tracker):
	return frappe.db.get_value(
		"Tracker Installation",
		{"vehicle": vehicle, "tracker": tracker},
		"name",
		order_by="modified desc",
	)


def sim_for_tracker_vehicle(tracker, vehicle):
	return frappe.db.get_value(
		"SIM Profile",
		{"current_tracker": tracker, "current_vehicle": vehicle},
		"name",
	)


@frappe.whitelist()
def create_telematics_links_for_installed_trackers(provider_account=None):
	provider_account = provider_account or ensure_imported_fleet_provider_account()
	provider = frappe.db.get_value("Telematics Provider Account", provider_account, "provider")
	created = []
	updated = []
	skipped = []

	trackers = frappe.get_all(
		"Tracker Profile",
		filters={"current_vehicle": ["is", "set"]},
		fields=["name", "imei", "current_customer", "current_vehicle", "tracker_name"],
		limit=500,
	)
	for tracker in trackers:
		if not tracker.current_vehicle or not tracker.imei:
			skipped.append(tracker.name)
			continue

		existing = frappe.db.exists(
			"Telematics Unit Link",
			{
				"provider_account": provider_account,
				"external_unit_id": tracker.imei,
			},
		)
		if existing:
			doc = frappe.get_doc("Telematics Unit Link", existing)
			is_new = False
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Telematics Unit Link",
					"naming_series": "TUL-.YYYY.-.####",
					"provider_account": provider_account,
					"external_unit_id": tracker.imei,
				}
			)
			is_new = True

		doc.provider = provider
		doc.status = "Active"
		doc.customer = tracker.current_customer
		doc.vehicle = tracker.current_vehicle
		doc.tracker = tracker.name
		doc.sim = sim_for_tracker_vehicle(tracker.name, tracker.current_vehicle)
		doc.installation = latest_installation_for_vehicle(tracker.current_vehicle, tracker.name)
		doc.external_unit_name = tracker.tracker_name or tracker.current_vehicle
		doc.external_device_id = tracker.imei
		doc.external_imei = tracker.imei
		doc.external_group = tracker.current_customer
		doc.timezone = "Africa/Harare"
		doc.sync_enabled = 0
		doc.last_sync_status = "Never Synced"
		doc.notes = "Created from imported Omni v3 tracker assignment. Confirm against live provider before enabling sync."

		if is_new:
			doc.insert(ignore_permissions=True)
			created.append(doc.name)
		else:
			doc.save(ignore_permissions=True)
			updated.append(doc.name)

	frappe.db.commit()
	return {"provider_account": provider_account, "created": created, "updated": updated, "skipped": skipped}
