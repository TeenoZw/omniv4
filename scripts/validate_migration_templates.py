#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


REQUIRED_HEADERS = {
	"01_customers_from_hubs.csv": ["legacy_hub_id", "customer_name", "customer_code"],
	"02_customer_fleet_profiles_from_hubs.csv": ["legacy_hub_id", "customer", "company"],
	"03_tracker_profiles_from_hardware.csv": ["legacy_hardware_id", "imei", "item_code"],
	"04_sim_profiles_from_sim_inventory.csv": ["legacy_sim_id", "iccid", "carrier"],
	"05_fleet_vehicles_from_vehicles.csv": ["legacy_vehicle_id", "legacy_hub_id", "registration_number"],
	"06_tracker_installations_from_assignments.csv": ["legacy_assignment_id", "legacy_hardware_id", "tracker_imei"],
	"07_sales_pipeline_from_enquiries.csv": ["legacy_enquiry_id", "status", "email"],
	"08_billing_subscriptions.csv": ["legacy_subscription_id", "legacy_hub_id", "item_code"],
}

REFERENCE_RULES = {
	"02_customer_fleet_profiles_from_hubs.csv": [("legacy_hub_id", "01_customers_from_hubs.csv", "legacy_hub_id")],
	"03_tracker_profiles_from_hardware.csv": [
		("current_customer_legacy_hub_id", "01_customers_from_hubs.csv", "legacy_hub_id"),
		("current_vehicle_legacy_vehicle_id", "05_fleet_vehicles_from_vehicles.csv", "legacy_vehicle_id"),
	],
	"04_sim_profiles_from_sim_inventory.csv": [
		("current_tracker_legacy_hardware_id", "03_tracker_profiles_from_hardware.csv", "legacy_hardware_id"),
		("current_customer_legacy_hub_id", "01_customers_from_hubs.csv", "legacy_hub_id"),
		("current_vehicle_legacy_vehicle_id", "05_fleet_vehicles_from_vehicles.csv", "legacy_vehicle_id"),
	],
	"05_fleet_vehicles_from_vehicles.csv": [("legacy_hub_id", "01_customers_from_hubs.csv", "legacy_hub_id")],
	"06_tracker_installations_from_assignments.csv": [
		("legacy_hub_id", "01_customers_from_hubs.csv", "legacy_hub_id"),
		("legacy_vehicle_id", "05_fleet_vehicles_from_vehicles.csv", "legacy_vehicle_id"),
		("legacy_hardware_id", "03_tracker_profiles_from_hardware.csv", "legacy_hardware_id"),
		("legacy_sim_id", "04_sim_profiles_from_sim_inventory.csv", "legacy_sim_id"),
	],
	"08_billing_subscriptions.csv": [("legacy_hub_id", "01_customers_from_hubs.csv", "legacy_hub_id")],
}


def read_rows(path):
	with path.open(newline="") as handle:
		return list(csv.DictReader(handle))


def validate_template_dir(template_dir):
	errors = []
	rows_by_file = {}

	for filename, required_headers in REQUIRED_HEADERS.items():
		path = template_dir / filename
		if not path.exists():
			errors.append(f"{filename}: missing file")
			continue

		rows = read_rows(path)
		rows_by_file[filename] = rows
		headers = rows[0].keys() if rows else csv.DictReader(path.open()).fieldnames or []
		for header in required_headers:
			if header not in headers:
				errors.append(f"{filename}: missing required header '{header}'")

		legacy_header = required_headers[0]
		seen = set()
		for index, row in enumerate(rows, start=2):
			value = (row.get(legacy_header) or "").strip()
			if not value:
				errors.append(f"{filename}:{index}: missing {legacy_header}")
			elif value in seen:
				errors.append(f"{filename}:{index}: duplicate {legacy_header} '{value}'")
			seen.add(value)

	for filename, rules in REFERENCE_RULES.items():
		for source_field, target_file, target_field in rules:
			target_values = {
				(row.get(target_field) or "").strip()
				for row in rows_by_file.get(target_file, [])
				if (row.get(target_field) or "").strip()
			}
			for index, row in enumerate(rows_by_file.get(filename, []), start=2):
				value = (row.get(source_field) or "").strip()
				if value and value not in target_values:
					errors.append(f"{filename}:{index}: {source_field} '{value}' not found in {target_file}.{target_field}")

	return errors


def main():
	parser = argparse.ArgumentParser(description="Validate Omni v3 to Omni v4 migration staging CSV files.")
	parser.add_argument(
		"template_dir",
		nargs="?",
		default="docs/migration_templates",
		help="Directory containing migration CSV templates.",
	)
	args = parser.parse_args()

	template_dir = Path(args.template_dir)
	errors = validate_template_dir(template_dir)
	if errors:
		print("Migration template validation failed:")
		for error in errors:
			print(f"- {error}")
		raise SystemExit(1)

	print(f"Migration template validation passed for {template_dir}.")


if __name__ == "__main__":
	main()

