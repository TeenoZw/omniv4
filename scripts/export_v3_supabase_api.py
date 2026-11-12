#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


CORE_TABLES = {
	"users", "hubs", "hub_memberships", "subscriptions", "technicians",
	"vehicles", "devices", "trips", "telemetry", "enquiries",
	"hardware_inventory", "hardware_assignments", "sim_inventory",
	"sim_assignments", "device_pairings", "technician_jobs",
	"admin_activity_logs", "data_subject_requests", "security_incidents",
	"compliance_attachments", "v4_companies", "v4_parties", "v4_items",
	"v4_document_sequences", "v4_fiscal_periods", "v4_accounts",
	"v4_documents", "v4_document_lines", "v4_journal_entries",
	"v4_journal_lines", "v4_warehouses", "v4_stock_movements",
}

EXCLUDED_TABLES = {"alembic_version", "refresh_tokens"}


def request_json(url, key, headers=None):
	request = urllib.request.Request(
		url,
		headers={
			"apikey": key,
			"Authorization": f"Bearer {key}",
			"Accept": "application/json",
			**(headers or {}),
		},
	)
	with urllib.request.urlopen(request, timeout=60) as response:
		return json.load(response), dict(response.headers)


def discover_tables(base_url, key):
	payload, _ = request_json(f"{base_url}/rest/v1/", key)
	paths = payload.get("paths", {})
	return {
		path.removeprefix("/")
		for path in paths
		if path.startswith("/")
		and not path.startswith("/rpc/")
		and path.count("/") == 1
		and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", path.removeprefix("/"))
		and path.removeprefix("/") not in EXCLUDED_TABLES
	}


def export_table(base_url, key, table, output_dir, page_size):
	rows = []
	offset = 0
	encoded_table = urllib.parse.quote(table, safe="")
	while True:
		url = f"{base_url}/rest/v1/{encoded_table}?select=*&order=id.asc&limit={page_size}&offset={offset}"
		page, _ = request_json(url, key, {"Prefer": "count=exact"})
		if not isinstance(page, list):
			raise RuntimeError(f"Unexpected response for {table}")
		rows.extend(page)
		if len(page) < page_size:
			break
		offset += page_size

	json_path = output_dir / f"{table}_rows.json"
	json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")

	if rows:
		headers = list(rows[0])
		for row in rows[1:]:
			for field in row:
				if field not in headers:
					headers.append(field)
	else:
		headers = []

	csv_path = output_dir / f"{table}_rows.csv"
	with csv_path.open("w", newline="", encoding="utf-8") as handle:
		if headers:
			writer = csv.DictWriter(handle, fieldnames=headers)
			writer.writeheader()
			for row in rows:
				writer.writerow({
					field: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
					for field, value in row.items()
				})
	return len(rows)


def main():
	parser = argparse.ArgumentParser(description="Export the legacy Supabase public schema over HTTPS.")
	parser.add_argument("--output-dir", type=Path)
	parser.add_argument("--page-size", type=int, default=1000)
	args = parser.parse_args()

	base_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
	key = os.environ.get("SUPABASE_SECRET_KEY", "")
	if not base_url or not key:
		print("SUPABASE_URL and SUPABASE_SECRET_KEY are required.", file=sys.stderr)
		return 1

	stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
	output_dir = args.output_dir or Path("migration_exports") / stamp
	output_dir.mkdir(parents=True, exist_ok=False)
	output_dir.chmod(0o700)

	discovered = discover_tables(base_url, key)
	tables = sorted(discovered | CORE_TABLES)
	manifest = []
	counts = []
	for table in tables:
		if table not in discovered:
			manifest.append({"table": table, "status": "missing", "detail": "Not exposed by the public Data API"})
			continue
		try:
			count = export_table(base_url, key, table, output_dir, args.page_size)
			manifest.append({"table": table, "status": "exported", "detail": ""})
			counts.append({"table": table, "row_count": count})
			print(f"{table}: {count}")
		except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError) as exc:
			manifest.append({"table": table, "status": "failed", "detail": str(exc)})
			print(f"{table}: failed", file=sys.stderr)

	with (output_dir / "source_counts.csv").open("w", newline="", encoding="utf-8") as handle:
		writer = csv.DictWriter(handle, fieldnames=["table", "row_count"])
		writer.writeheader()
		writer.writerows(counts)
	with (output_dir / "export_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
		writer = csv.DictWriter(handle, fieldnames=["table", "status", "detail"])
		writer.writeheader()
		writer.writerows(manifest)

	for path in output_dir.iterdir():
		path.chmod(0o600)
	print(f"Export complete: {output_dir}")
	return 1 if any(row["status"] == "failed" for row in manifest) else 0


if __name__ == "__main__":
	raise SystemExit(main())
