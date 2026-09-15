from datetime import datetime

import frappe
from frappe.utils import get_datetime, now_datetime

from omni_operations.telematics.providers.registry import get_provider


@frappe.whitelist()
def sync_provider_units(provider_account_name):
	provider_account = frappe.get_doc("Telematics Provider Account", provider_account_name)
	provider = get_provider(provider_account.name)
	started = now_datetime()
	processed = 0
	updated = 0
	failed = 0
	ignored = 0
	ignored_unit_ids = _ignored_external_unit_ids(provider_account)

	try:
		units = provider.list_units()
		for unit in units:
			processed += 1
			if unit.external_unit_id in ignored_unit_ids:
				ignored += 1
				continue

			unit_link_name = frappe.db.exists(
				"Telematics Unit Link",
				{
					"provider_account": provider_account.name,
					"external_unit_id": unit.external_unit_id,
				},
			)

			if not unit_link_name:
				failed += 1
				continue

			update_values = {
				"external_unit_name": unit.external_unit_name,
				"external_device_id": unit.external_device_id,
				"external_imei": unit.external_imei,
				"external_group": unit.external_group,
				"timezone": unit.timezone,
				"last_sync_datetime": now_datetime(),
				"last_sync_status": "Success",
				"last_error": None,
			}
			sync_enabled = frappe.db.get_value("Telematics Unit Link", unit_link_name, "sync_enabled")
			if sync_enabled and unit.position:
				update_values.update(_position_update_values(unit.position))

			frappe.db.set_value(
				"Telematics Unit Link",
				unit_link_name,
				update_values,
			)
			updated += 1

		status = "Success" if failed == 0 else "Warning"
		error_message = None if failed == 0 else f"{failed} provider unit(s) could not be matched to Omni unit links."
	except Exception as exc:
		status = "Failed"
		error_message = str(exc)

	log = frappe.get_doc(
		{
			"doctype": "Telematics Sync Log",
			"provider_account": provider_account.name,
			"sync_type": "Unit Metadata",
			"status": status,
			"started_datetime": started,
			"finished_datetime": now_datetime(),
			"records_processed": processed,
			"records_updated": updated,
			"records_failed": failed,
			"request_summary": f"Pulled unit metadata from {provider_account.provider}.",
			"response_summary": f"Processed {processed}; updated {updated}; ignored {ignored}; failed {failed}.",
			"error_message": error_message,
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"status": status,
		"sync_log": log.name,
		"records_processed": processed,
		"records_updated": updated,
		"records_ignored": ignored,
		"records_failed": failed,
	}


@frappe.whitelist()
def check_provider_connection(provider_account_name):
	provider_account = frappe.get_doc("Telematics Provider Account", provider_account_name)
	provider = get_provider(provider_account.name)
	started = now_datetime()

	try:
		is_connected = provider.check_connection()
		status = "Success" if is_connected else "Failed"
		error_message = None if is_connected else "Provider returned an unsuccessful connection check."
	except Exception as exc:
		status = "Failed"
		error_message = str(exc)

	frappe.db.set_value(
		"Telematics Provider Account",
		provider_account.name,
		{
			"last_sync_datetime": now_datetime(),
			"last_sync_status": status,
			"last_error": error_message,
		},
	)
	log = frappe.get_doc(
		{
			"doctype": "Telematics Sync Log",
			"provider_account": provider_account.name,
			"sync_type": "Account Check",
			"status": status,
			"started_datetime": started,
			"finished_datetime": now_datetime(),
			"records_processed": 1,
			"records_updated": 1 if status == "Success" else 0,
			"records_failed": 0 if status == "Success" else 1,
			"request_summary": f"Checked connection for {provider_account.provider}.",
			"response_summary": status,
			"error_message": error_message,
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"status": status,
		"sync_log": log.name,
		"error_message": error_message,
	}


@frappe.whitelist()
def preview_provider_units(provider_account_name):
	provider_account = frappe.get_doc("Telematics Provider Account", provider_account_name)
	provider = get_provider(provider_account.name)
	units = provider.list_units()
	rows = []
	ignored_unit_ids = _ignored_external_unit_ids(provider_account)

	for unit in units:
		is_ignored = unit.external_unit_id in ignored_unit_ids
		unit_link = frappe.db.get_value(
			"Telematics Unit Link",
			{
				"provider_account": provider_account.name,
				"external_unit_id": unit.external_unit_id,
			},
			["name", "vehicle", "customer", "sync_enabled", "last_sync_status"],
			as_dict=True,
		)
		rows.append(
			{
				"external_unit_id": unit.external_unit_id,
				"external_unit_name": unit.external_unit_name,
				"external_device_id": unit.external_device_id,
				"external_imei": unit.external_imei,
				"matched": bool(unit_link),
				"ignored": is_ignored,
				"unit_link": unit_link.name if unit_link else None,
				"vehicle": unit_link.vehicle if unit_link else None,
				"customer": unit_link.customer if unit_link else None,
				"sync_enabled": unit_link.sync_enabled if unit_link else None,
				"last_sync_status": unit_link.last_sync_status if unit_link else None,
			}
		)

	return {
		"provider_account": provider_account.name,
		"provider": provider_account.provider,
		"total_units": len(rows),
		"matched_units": len([row for row in rows if row["matched"]]),
		"ignored_units": len([row for row in rows if row["ignored"]]),
		"unmatched_units": len([row for row in rows if not row["matched"] and not row["ignored"]]),
		"units": rows,
	}


@frappe.whitelist()
def create_provider_unit_links(provider_account_name, links):
	created = []
	updated = []

	for link in links:
		unit_link_name = frappe.db.exists(
			"Telematics Unit Link",
			{
				"provider_account": provider_account_name,
				"external_unit_id": link.get("external_unit_id"),
			},
		)
		values = {
			"vehicle": link.get("vehicle"),
			"external_unit_name": link.get("external_unit_name"),
			"sync_enabled": link.get("sync_enabled", 1),
			"status": link.get("status", "Active"),
		}

		if unit_link_name:
			frappe.db.set_value("Telematics Unit Link", unit_link_name, values)
			updated.append(unit_link_name)
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Telematics Unit Link",
				"provider_account": provider_account_name,
				"vehicle": link.get("vehicle"),
				"external_unit_id": link.get("external_unit_id"),
				"external_unit_name": link.get("external_unit_name"),
				"sync_enabled": link.get("sync_enabled", 1),
				"status": link.get("status", "Active"),
			}
		).insert()
		created.append(doc.name)

	frappe.db.commit()

	return {
		"created": created,
		"updated": updated,
	}


@frappe.whitelist()
def sync_vehicle_telematics(vehicle):
	unit_links = frappe.get_all(
		"Telematics Unit Link",
		filters={"vehicle": vehicle, "sync_enabled": 1},
		pluck="provider_account",
	)
	results = []

	for provider_account in sorted(set(unit_links)):
		results.append(sync_provider_units(provider_account))

	return results


def _position_update_values(position):
	update_values = {}

	if position.get("latitude") is not None:
		update_values["latitude"] = position.get("latitude")
	if position.get("longitude") is not None:
		update_values["longitude"] = position.get("longitude")
	if position.get("speed") is not None:
		update_values["speed"] = position.get("speed")
	if position.get("ignition") is not None:
		update_values["ignition"] = position.get("ignition")
	if position.get("odometer") is not None:
		update_values["odometer"] = position.get("odometer")
	if position.get("timestamp"):
		update_values["last_position_datetime"] = _position_datetime(position.get("timestamp"))

	return update_values


def _position_datetime(value):
	if isinstance(value, (int, float)):
		return get_datetime(datetime.fromtimestamp(value))
	return get_datetime(value)


def _ignored_external_unit_ids(provider_account):
	raw_value = provider_account.get("ignored_external_unit_ids") or ""
	return {unit_id.strip() for unit_id in raw_value.replace(",", "\n").splitlines() if unit_id.strip()}
