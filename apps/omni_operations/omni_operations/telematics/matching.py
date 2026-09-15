import csv
from pathlib import Path

import frappe
from frappe.utils import get_datetime, now_datetime


REQUIRED_HEADERS = [
	"provider_account",
	"external_unit_id",
	"external_unit_name",
	"external_device_id",
	"external_imei",
]


def clean(value):
	return str(value or "").strip()


def normalise_datetime(value):
	value = clean(value)
	if not value:
		return None
	if "+" in value:
		value = value.split("+", 1)[0]
	if value.endswith("Z"):
		value = value[:-1]
	try:
		return get_datetime(value)
	except Exception:
		return None


def normalise_bool(value):
	return 1 if clean(value).lower() in {"1", "true", "yes", "on"} else 0


def normalise_float(value):
	try:
		return float(clean(value))
	except Exception:
		return None


def read_provider_units(path):
	path = Path(path)
	if not path.exists():
		frappe.throw(f"Provider unit CSV not found: {path}")

	with path.open(newline="", encoding="utf-8-sig") as handle:
		reader = csv.DictReader(handle)
		headers = reader.fieldnames or []
		missing = [header for header in REQUIRED_HEADERS if header not in headers]
		if missing:
			frappe.throw(f"Provider unit CSV missing headers: {', '.join(missing)}")
		return list(reader)


def tracker_for_provider_row(row):
	imei = clean(row.get("external_imei")) or clean(row.get("external_device_id")) or clean(row.get("external_unit_id"))
	if not imei:
		return None
	return frappe.db.get_value(
		"Tracker Profile",
		{"imei": imei},
		["name", "current_customer", "current_vehicle"],
		as_dict=True,
	)


@frappe.whitelist()
def preview_provider_unit_matches(csv_path):
	rows = read_provider_units(csv_path)
	matches = []
	unmatched = []
	for row in rows:
		tracker = tracker_for_provider_row(row)
		if tracker and tracker.current_vehicle:
			matches.append(
				{
					"external_unit_id": clean(row.get("external_unit_id")),
					"external_imei": clean(row.get("external_imei")),
					"tracker": tracker.name,
					"customer": tracker.current_customer,
					"vehicle": tracker.current_vehicle,
				}
			)
		else:
			unmatched.append(
				{
					"external_unit_id": clean(row.get("external_unit_id")),
					"external_imei": clean(row.get("external_imei")),
					"reason": "No installed Tracker Profile matched by IMEI.",
				}
			)

	return {"rows": len(rows), "matches": matches, "unmatched": unmatched}


@frappe.whitelist()
def apply_provider_unit_matches(csv_path, enable_sync=0):
	rows = read_provider_units(csv_path)
	created = []
	updated = []
	unmatched = []
	enable_sync = normalise_bool(enable_sync)

	for row in rows:
		tracker = tracker_for_provider_row(row)
		if not tracker or not tracker.current_vehicle:
			unmatched.append(clean(row.get("external_unit_id")) or clean(row.get("external_imei")))
			continue

		provider_account = clean(row.get("provider_account"))
		if not provider_account or not frappe.db.exists("Telematics Provider Account", provider_account):
			unmatched.append(clean(row.get("external_unit_id")) or clean(row.get("external_imei")))
			continue

		external_unit_id = clean(row.get("external_unit_id")) or clean(row.get("external_imei"))
		existing = frappe.db.exists(
			"Telematics Unit Link",
			{
				"provider_account": provider_account,
				"external_unit_id": external_unit_id,
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
					"external_unit_id": external_unit_id,
				}
			)
			is_new = True

		doc.customer = tracker.current_customer
		doc.vehicle = tracker.current_vehicle
		doc.tracker = tracker.name
		doc.sim = frappe.db.get_value(
			"SIM Profile",
			{"current_tracker": tracker.name, "current_vehicle": tracker.current_vehicle},
			"name",
		)
		doc.external_unit_name = clean(row.get("external_unit_name")) or tracker.current_vehicle
		doc.external_device_id = clean(row.get("external_device_id"))
		doc.external_imei = clean(row.get("external_imei")) or tracker.name
		doc.external_group = clean(row.get("external_group"))
		doc.timezone = clean(row.get("timezone")) or "Africa/Harare"
		doc.sync_enabled = enable_sync
		doc.last_position_datetime = normalise_datetime(row.get("last_position_datetime"))
		doc.latitude = normalise_float(row.get("latitude"))
		doc.longitude = normalise_float(row.get("longitude"))
		doc.speed = normalise_float(row.get("speed"))
		doc.ignition = normalise_bool(row.get("ignition"))
		doc.odometer = normalise_float(row.get("odometer"))
		doc.last_sync_datetime = now_datetime()
		doc.last_sync_status = "Success"
		doc.last_error = None
		doc.notes = "Matched from provider unit CSV. Review before enabling live sync." if not enable_sync else "Matched from provider unit CSV."

		if is_new:
			doc.insert(ignore_permissions=True)
			created.append(doc.name)
		else:
			doc.save(ignore_permissions=True)
			updated.append(doc.name)

	frappe.db.commit()
	return {"created": created, "updated": updated, "unmatched": unmatched}
