#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


HEADERS = [
	"provider_account",
	"external_unit_id",
	"external_unit_name",
	"external_device_id",
	"external_imei",
	"external_group",
	"timezone",
	"last_position_datetime",
	"latitude",
	"longitude",
	"speed",
	"ignition",
	"odometer",
]


def main():
	parser = argparse.ArgumentParser(description="Create a provider-unit CSV skeleton from tracker staging rows.")
	parser.add_argument("--trackers", default="migration_working/omniv4_staging/03_tracker_profiles_from_hardware.csv")
	parser.add_argument("--output", default="migration_working/omniv4_staging/09_telematics_provider_units_prefill.csv")
	parser.add_argument("--provider-account", default="Imported Fleet Telematics Staging")
	args = parser.parse_args()

	with open(args.trackers, newline="", encoding="utf-8") as handle:
		tracker_rows = list(csv.DictReader(handle))

	Path(args.output).parent.mkdir(parents=True, exist_ok=True)
	with open(args.output, "w", newline="", encoding="utf-8") as handle:
		writer = csv.DictWriter(handle, fieldnames=HEADERS)
		writer.writeheader()
		for row in tracker_rows:
			imei = (row.get("imei") or "").strip()
			if not imei or not (row.get("current_vehicle_legacy_vehicle_id") or "").strip():
				continue
			writer.writerow(
				{
					"provider_account": args.provider_account,
					"external_unit_id": imei,
					"external_unit_name": row.get("model") or row.get("hardware_type") or imei,
					"external_device_id": imei,
					"external_imei": imei,
					"external_group": row.get("current_customer_legacy_hub_id") or "",
					"timezone": "Africa/Harare",
				}
			)

	print(f"Wrote {args.output}")


if __name__ == "__main__":
	main()
