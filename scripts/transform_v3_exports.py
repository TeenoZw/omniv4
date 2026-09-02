#!/usr/bin/env python3
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


TEMPLATE_HEADERS = {
	"01_customers_from_hubs.csv": [
		"legacy_hub_id",
		"customer_name",
		"customer_code",
		"customer_group",
		"status",
		"country",
		"city",
		"address_line",
		"location",
		"timezone",
		"currency",
		"go_live_date",
		"primary_contact_name",
		"primary_contact_email",
		"primary_contact_phone",
		"billing_contact_name",
		"billing_contact_email",
		"billing_contact_phone",
		"subscription_tier",
		"billing_cycle",
		"payment_method",
		"notes",
	],
	"02_customer_fleet_profiles_from_hubs.csv": [
		"legacy_hub_id",
		"customer",
		"company",
		"profile_status",
		"go_live_date",
		"timezone",
		"expected_vehicle_count",
		"expected_tracker_count",
		"primary_contact_name",
		"primary_contact_email",
		"primary_contact_phone",
		"billing_contact_name",
		"billing_contact_email",
		"billing_contact_phone",
		"notes",
	],
	"03_tracker_profiles_from_hardware.csv": [
		"legacy_hardware_id",
		"imei",
		"serial_number",
		"item_code",
		"hardware_type",
		"model",
		"manufacturer",
		"firmware_version",
		"purchase_date",
		"purchase_cost",
		"status",
		"current_customer_legacy_hub_id",
		"current_vehicle_legacy_vehicle_id",
		"notes",
	],
	"04_sim_profiles_from_sim_inventory.csv": [
		"legacy_sim_id",
		"iccid",
		"msisdn",
		"item_code",
		"serial_number",
		"carrier",
		"apn",
		"roaming_enabled",
		"roaming_regions",
		"status",
		"current_tracker_legacy_hardware_id",
		"current_customer_legacy_hub_id",
		"current_vehicle_legacy_vehicle_id",
		"notes",
	],
	"05_fleet_vehicles_from_vehicles.csv": [
		"legacy_vehicle_id",
		"legacy_hub_id",
		"customer",
		"registration_number",
		"vin",
		"asset_type",
		"asset_type_other",
		"asset_name",
		"make",
		"model",
		"year",
		"color",
		"fuel_type",
		"engine_capacity",
		"co2_emissions",
		"status",
		"legacy_tracker_imei",
		"source_job_legacy_id",
		"photo_url",
		"notes",
	],
	"06_tracker_installations_from_assignments.csv": [
		"legacy_assignment_id",
		"legacy_pairing_id",
		"legacy_hub_id",
		"legacy_vehicle_id",
		"legacy_hardware_id",
		"legacy_sim_id",
		"customer",
		"vehicle",
		"tracker_imei",
		"sim_iccid",
		"status",
		"assigned_at",
		"installed_at",
		"installation_location",
		"installation_latitude",
		"installation_longitude",
		"requested_by",
		"approved_by",
		"technician",
		"notes",
	],
	"07_sales_pipeline_from_enquiries.csv": [
		"legacy_enquiry_id",
		"status",
		"customer_type",
		"full_name",
		"email",
		"phone",
		"company_name",
		"fleet_size",
		"operating_area",
		"preferred_contact_method",
		"expected_go_live_date",
		"tracking_use_case",
		"hardware_choices",
		"add_ons",
		"quoted_monthly",
		"quoted_hardware_total",
		"quote_sent_at",
		"responded_at",
		"closed_at",
		"terms_accepted",
		"privacy_accepted",
		"message",
		"admin_notes",
		"target_customer",
	],
	"08_billing_subscriptions.csv": [
		"legacy_subscription_id",
		"legacy_hub_id",
		"customer",
		"user_email",
		"tier",
		"item_code",
		"start_date",
		"end_date",
		"is_active",
		"auto_renew",
		"billing_cycle",
		"payment_method",
		"subscription_tier",
		"notes",
	],
}


def read_csv(path):
	if not path.exists():
		return []
	with path.open(newline="", encoding="utf-8-sig") as handle:
		return list(csv.DictReader(handle))


def write_csv(path, rows):
	path.parent.mkdir(parents=True, exist_ok=True)
	headers = TEMPLATE_HEADERS[path.name]
	with path.open("w", newline="", encoding="utf-8") as handle:
		writer = csv.DictWriter(handle, fieldnames=headers)
		writer.writeheader()
		for row in rows:
			writer.writerow({header: row.get(header, "") for header in headers})


def clean(value):
	return (value or "").strip()


def item_code_for_hardware(row):
	model = clean(row.get("model")).upper().replace(" ", "-")
	hardware_type = clean(row.get("hardware_type")).upper().replace(" ", "-")
	return model or hardware_type or "TRACKER-HW-4G"


def parse_asset_notes(notes):
	data = {}
	for line in (notes or "").splitlines():
		if ":" not in line or line.startswith("["):
			continue
		key, value = line.split(":", 1)
		data[key.strip().lower()] = value.strip()
	return data


def parse_json_list(value):
	if not clean(value):
		return ""
	try:
		decoded = json.loads(value)
	except json.JSONDecodeError:
		return value
	if isinstance(decoded, list):
		return "; ".join(str(item) for item in decoded)
	return str(decoded)


def customer_name(hub):
	return clean(hub.get("name"))


def build_vehicle_key(assignment):
	if clean(assignment.get("vehicle_id")):
		return clean(assignment.get("vehicle_id"))
	if clean(assignment.get("asset_registration")):
		return f"asset-registration:{clean(assignment.get('asset_registration')).upper()}"
	if clean(assignment.get("asset_label")):
		return f"asset-label:{clean(assignment.get('asset_label')).upper()}"
	return f"assignment:{clean(assignment.get('id'))}"


def transform(input_dir, output_dir):
	hubs = read_csv(input_dir / "hubs_rows.csv")
	users = read_csv(input_dir / "users_rows.csv")
	enquiries = read_csv(input_dir / "enquiries_rows.csv")
	hardware = read_csv(input_dir / "hardware_inventory_rows.csv")
	hardware_assignments = read_csv(input_dir / "hardware_assignments_rows.csv")
	sims = read_csv(input_dir / "sim_inventory_rows.csv")
	sim_assignments = read_csv(input_dir / "sim_assignments_rows.csv")
	subscriptions = read_csv(input_dir / "subscriptions_rows.csv")

	hubs_by_id = {clean(row.get("id")): row for row in hubs}
	users_by_id = {clean(row.get("id")): row for row in users}
	hardware_by_id = {clean(row.get("id")): row for row in hardware}
	sims_by_id = {clean(row.get("id")): row for row in sims}

	active_hw_assignment_by_hardware = {
		clean(row.get("hardware_id")): row for row in hardware_assignments if clean(row.get("is_active")).lower() == "true"
	}
	active_sim_assignment_by_sim = {
		clean(row.get("sim_id")): row for row in sim_assignments if clean(row.get("is_active")).lower() == "true"
	}
	active_sim_assignment_by_hardware = {
		clean(row.get("hardware_id")): row for row in sim_assignments if clean(row.get("is_active")).lower() == "true"
	}

	vehicle_id_by_assignment_id = {}
	vehicle_rows_by_key = {}
	vehicle_source_assignment_by_key = {}
	for assignment in hardware_assignments:
		if not clean(assignment.get("hub_id")):
			continue
		key = build_vehicle_key(assignment)
		legacy_vehicle_id = key.replace(":", "-")
		vehicle_id_by_assignment_id[clean(assignment.get("id"))] = legacy_vehicle_id
		is_active_assignment = clean(assignment.get("is_active")).lower() == "true"
		existing_assignment = vehicle_source_assignment_by_key.get(key)
		existing_is_active = clean((existing_assignment or {}).get("is_active")).lower() == "true"
		if key in vehicle_rows_by_key and (existing_is_active or not is_active_assignment):
			continue

		asset = parse_asset_notes(assignment.get("notes"))
		hub = hubs_by_id.get(clean(assignment.get("hub_id")), {})
		hw = hardware_by_id.get(clean(assignment.get("hardware_id")), {})
		asset_type = asset.get("type") or "vehicle"
		vehicle_rows_by_key[key] = {
			"legacy_vehicle_id": legacy_vehicle_id,
			"legacy_hub_id": clean(assignment.get("hub_id")),
			"customer": customer_name(hub),
			"registration_number": clean(assignment.get("asset_registration")),
			"vin": asset.get("vin"),
			"asset_type": asset_type,
			"asset_type_other": "" if asset_type == "vehicle" else asset_type,
			"asset_name": clean(assignment.get("asset_label")) or asset.get("name"),
			"make": asset.get("make"),
			"model": asset.get("model"),
			"year": asset.get("year"),
			"color": asset.get("color"),
			"fuel_type": asset.get("fuel_type"),
			"engine_capacity": asset.get("engine_capacity"),
			"co2_emissions": asset.get("co2_emissions"),
			"status": "active" if is_active_assignment else "inactive",
			"legacy_tracker_imei": clean(hw.get("imei")),
			"source_job_legacy_id": "",
			"photo_url": "",
			"notes": clean(assignment.get("notes")),
		}
		vehicle_source_assignment_by_key[key] = assignment

	customer_rows = []
	profile_rows = []
	for hub in hubs:
		notes = clean(hub.get("notes"))
		if clean(hub.get("deleted_at")):
			notes = f"{notes}\nLegacy deleted_at: {clean(hub.get('deleted_at'))}".strip()
		customer_rows.append(
			{
				"legacy_hub_id": clean(hub.get("id")),
				"customer_name": customer_name(hub),
				"customer_code": clean(hub.get("code")),
				"customer_group": clean(hub.get("hub_type")) or "business",
				"status": clean(hub.get("status")) or "active",
				"country": clean(hub.get("country")),
				"city": clean(hub.get("city")),
				"address_line": clean(hub.get("address_line")),
				"location": clean(hub.get("location")),
				"timezone": clean(hub.get("timezone")),
				"currency": clean(hub.get("currency")) or "USD",
				"go_live_date": clean(hub.get("go_live_date")),
				"primary_contact_name": clean(hub.get("primary_contact_name")),
				"primary_contact_email": clean(hub.get("primary_contact_email")),
				"primary_contact_phone": clean(hub.get("primary_contact_phone")),
				"billing_contact_name": clean(hub.get("billing_contact_name")),
				"billing_contact_email": clean(hub.get("billing_contact_email")),
				"billing_contact_phone": clean(hub.get("billing_contact_phone")),
				"subscription_tier": clean(hub.get("subscription_tier")),
				"billing_cycle": clean(hub.get("billing_cycle")),
				"payment_method": clean(hub.get("payment_method")),
				"notes": notes,
			}
		)
		profile_rows.append(
			{
				"legacy_hub_id": clean(hub.get("id")),
				"customer": customer_name(hub),
				"company": "Omni Logistics",
				"profile_status": clean(hub.get("status")) or "active",
				"go_live_date": clean(hub.get("go_live_date")),
				"timezone": clean(hub.get("timezone")),
				"expected_vehicle_count": clean(hub.get("vehicle_count")),
				"expected_tracker_count": clean(hub.get("device_count")),
				"primary_contact_name": clean(hub.get("primary_contact_name")),
				"primary_contact_email": clean(hub.get("primary_contact_email")),
				"primary_contact_phone": clean(hub.get("primary_contact_phone")),
				"billing_contact_name": clean(hub.get("billing_contact_name")),
				"billing_contact_email": clean(hub.get("billing_contact_email")),
				"billing_contact_phone": clean(hub.get("billing_contact_phone")),
				"notes": notes,
			}
		)

	tracker_rows = []
	for hw in hardware:
		active_assignment = active_hw_assignment_by_hardware.get(clean(hw.get("id")), {})
		vehicle_id = vehicle_id_by_assignment_id.get(clean(active_assignment.get("id")), "")
		tracker_rows.append(
			{
				"legacy_hardware_id": clean(hw.get("id")),
				"imei": clean(hw.get("imei")),
				"serial_number": clean(hw.get("serial_number")),
				"item_code": item_code_for_hardware(hw),
				"hardware_type": clean(hw.get("hardware_type")),
				"model": clean(hw.get("model")),
				"manufacturer": clean(hw.get("manufacturer")),
				"firmware_version": clean(hw.get("firmware_version")),
				"purchase_date": clean(hw.get("purchase_date")),
				"purchase_cost": clean(hw.get("purchase_cost")),
				"status": clean(hw.get("status")),
				"current_customer_legacy_hub_id": clean(active_assignment.get("hub_id")),
				"current_vehicle_legacy_vehicle_id": vehicle_id,
				"notes": clean(hw.get("notes")),
			}
		)

	sim_rows = []
	for sim in sims:
		active_assignment = active_sim_assignment_by_sim.get(clean(sim.get("id")), {})
		hw_assignment = active_hw_assignment_by_hardware.get(clean(active_assignment.get("hardware_id")), {})
		vehicle_id = vehicle_id_by_assignment_id.get(clean(hw_assignment.get("id")), "")
		sim_rows.append(
			{
				"legacy_sim_id": clean(sim.get("id")),
				"iccid": clean(sim.get("iccid")),
				"msisdn": clean(sim.get("msisdn")),
				"item_code": "SIM-IOT",
				"serial_number": clean(sim.get("iccid")),
				"carrier": clean(sim.get("carrier")),
				"apn": clean(sim.get("apn")),
				"roaming_enabled": clean(sim.get("roaming_enabled")),
				"roaming_regions": clean(sim.get("roaming_regions")),
				"status": clean(sim.get("status")),
				"current_tracker_legacy_hardware_id": clean(active_assignment.get("hardware_id")),
				"current_customer_legacy_hub_id": clean(active_assignment.get("hub_id")),
				"current_vehicle_legacy_vehicle_id": vehicle_id,
				"notes": clean(sim.get("notes")),
			}
		)

	installation_rows = []
	for assignment in hardware_assignments:
		hw = hardware_by_id.get(clean(assignment.get("hardware_id")), {})
		sim_assignment = active_sim_assignment_by_hardware.get(clean(assignment.get("hardware_id")), {})
		sim = sims_by_id.get(clean(sim_assignment.get("sim_id")), {})
		hub = hubs_by_id.get(clean(assignment.get("hub_id")), {})
		user = users_by_id.get(clean(assignment.get("assigned_by")), {})
		installation_rows.append(
			{
				"legacy_assignment_id": clean(assignment.get("id")),
				"legacy_pairing_id": "",
				"legacy_hub_id": clean(assignment.get("hub_id")),
				"legacy_vehicle_id": vehicle_id_by_assignment_id.get(clean(assignment.get("id")), ""),
				"legacy_hardware_id": clean(assignment.get("hardware_id")),
				"legacy_sim_id": clean(sim_assignment.get("sim_id")),
				"customer": customer_name(hub),
				"vehicle": clean(assignment.get("asset_registration")) or clean(assignment.get("asset_label")),
				"tracker_imei": clean(hw.get("imei")),
				"sim_iccid": clean(sim.get("iccid")),
				"status": "Completed" if clean(assignment.get("installed_at")) else "Assigned",
				"assigned_at": clean(assignment.get("assigned_at")),
				"installed_at": clean(assignment.get("installed_at")),
				"installation_location": clean(assignment.get("installation_location")),
				"installation_latitude": clean(assignment.get("installation_latitude")),
				"installation_longitude": clean(assignment.get("installation_longitude")),
				"requested_by": "",
				"approved_by": clean(user.get("email")),
				"technician": clean(user.get("email")),
				"notes": clean(assignment.get("notes")),
			}
		)

	enquiry_rows = []
	for enquiry in enquiries:
		target_customer = clean(enquiry.get("company_name")) or clean(enquiry.get("full_name"))
		enquiry_rows.append(
			{
				"legacy_enquiry_id": clean(enquiry.get("id")),
				"status": clean(enquiry.get("status")),
				"customer_type": clean(enquiry.get("customer_type")),
				"full_name": clean(enquiry.get("full_name")),
				"email": clean(enquiry.get("email")),
				"phone": clean(enquiry.get("phone")),
				"company_name": clean(enquiry.get("company_name")),
				"fleet_size": clean(enquiry.get("fleet_size")),
				"operating_area": clean(enquiry.get("operating_area")),
				"preferred_contact_method": clean(enquiry.get("preferred_contact_method")),
				"expected_go_live_date": clean(enquiry.get("expected_go_live_date")),
				"tracking_use_case": clean(enquiry.get("tracking_use_case")),
				"hardware_choices": parse_json_list(enquiry.get("hardware_choices")),
				"add_ons": parse_json_list(enquiry.get("add_ons")),
				"quoted_monthly": clean(enquiry.get("quoted_monthly")),
				"quoted_hardware_total": clean(enquiry.get("quoted_hardware_total")),
				"quote_sent_at": clean(enquiry.get("quote_sent_at")),
				"responded_at": clean(enquiry.get("responded_at")),
				"closed_at": clean(enquiry.get("closed_at")),
				"terms_accepted": clean(enquiry.get("terms_accepted")),
				"privacy_accepted": clean(enquiry.get("privacy_accepted")),
				"message": clean(enquiry.get("message")),
				"admin_notes": clean(enquiry.get("admin_notes")),
				"target_customer": target_customer,
			}
		)

	billing_rows = []
	for subscription in subscriptions:
		hub = hubs_by_id.get(clean(subscription.get("hub_id")), {})
		user = users_by_id.get(clean(subscription.get("user_id")), {})
		tier = clean(subscription.get("tier"))
		billing_rows.append(
			{
				"legacy_subscription_id": clean(subscription.get("id")),
				"legacy_hub_id": clean(subscription.get("hub_id")),
				"customer": customer_name(hub),
				"user_email": clean(user.get("email")),
				"tier": tier,
				"item_code": f"FLEET-SUB-{tier.upper()}" if tier else "FLEET-SUBSCRIPTION",
				"start_date": clean(subscription.get("start_date")),
				"end_date": clean(subscription.get("end_date")),
				"is_active": clean(subscription.get("is_active")),
				"auto_renew": clean(subscription.get("auto_renew")),
				"billing_cycle": clean(hub.get("billing_cycle")),
				"payment_method": clean(hub.get("payment_method")),
				"subscription_tier": clean(hub.get("subscription_tier")),
				"notes": "Imported as subscription history unless explicitly activated for ERPNext recurring billing.",
			}
		)

	output_rows = {
		"01_customers_from_hubs.csv": customer_rows,
		"02_customer_fleet_profiles_from_hubs.csv": profile_rows,
		"03_tracker_profiles_from_hardware.csv": tracker_rows,
		"04_sim_profiles_from_sim_inventory.csv": sim_rows,
		"05_fleet_vehicles_from_vehicles.csv": list(vehicle_rows_by_key.values()),
		"06_tracker_installations_from_assignments.csv": installation_rows,
		"07_sales_pipeline_from_enquiries.csv": enquiry_rows,
		"08_billing_subscriptions.csv": billing_rows,
	}

	for filename, rows in output_rows.items():
		write_csv(output_dir / filename, rows)

	report = {
		"source_counts": {
			"hubs": len(hubs),
			"users": len(users),
			"enquiries": len(enquiries),
			"hardware_inventory": len(hardware),
			"hardware_assignments": len(hardware_assignments),
			"sim_inventory": len(sims),
			"sim_assignments": len(sim_assignments),
			"subscriptions": len(subscriptions),
		},
		"output_counts": {filename: len(rows) for filename, rows in output_rows.items()},
		"missing_source_exports": [
			name
			for name in ["vehicles_rows.csv", "device_pairings_rows.csv", "technician_jobs_rows.csv"]
			if not (input_dir / name).exists()
		],
		"notes": [
			"Vehicle rows were derived from hardware assignment asset fields because vehicles_rows.csv was not present.",
			"When multiple assignments referenced the same derived vehicle, the active assignment was preferred for the vehicle master row.",
			"Device pairing IDs are blank because device_pairings_rows.csv was not present.",
			"Technician job references are blank because technician_jobs_rows.csv was not present.",
			"User password hashes were intentionally ignored.",
		],
	}
	(output_dir / "migration_transform_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
	return report


def main():
	parser = argparse.ArgumentParser(description="Transform Omni v3 CSV exports into Omni v4 migration staging CSVs.")
	parser.add_argument("--input-dir", default="migration_exports")
	parser.add_argument("--output-dir", default="migration_working/omniv4_staging")
	args = parser.parse_args()

	report = transform(Path(args.input_dir), Path(args.output_dir))
	print(json.dumps(report, indent=2))


if __name__ == "__main__":
	main()
