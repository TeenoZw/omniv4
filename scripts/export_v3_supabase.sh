#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${1:-$ROOT_DIR/.env.migration.local}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUTPUT_DIR="${2:-$ROOT_DIR/migration_exports/$STAMP}"
POSTGRES_IMAGE="${POSTGRES_IMAGE:-postgres:16-alpine}"

if [[ ! -f "$ENV_FILE" ]]; then
	printf 'Missing migration environment file: %s\n' "$ENV_FILE" >&2
	printf 'Create it with LEGACY_V3_DATABASE_URL=<Supabase PostgreSQL connection string>.\n' >&2
	exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ -z "${LEGACY_V3_DATABASE_URL:-}" ]]; then
	printf 'LEGACY_V3_DATABASE_URL is not set in %s\n' "$ENV_FILE" >&2
	exit 1
fi

mkdir -p "$OUTPUT_DIR"
chmod 700 "$OUTPUT_DIR"

tables=(
	users hubs hub_memberships subscriptions technicians vehicles devices
	enquiries hardware_inventory hardware_assignments sim_inventory sim_assignments
	device_pairings technician_jobs admin_activity_logs data_subject_requests
	security_incidents compliance_attachments v4_companies v4_parties v4_items
	v4_document_sequences v4_fiscal_periods v4_accounts v4_documents
	v4_document_lines v4_journal_entries v4_journal_lines v4_warehouses
	v4_stock_movements
)

docker run --rm \
	-e LEGACY_V3_DATABASE_URL \
	-v "$OUTPUT_DIR:/export" \
	"$POSTGRES_IMAGE" sh -euc '
		pg_dump --format=custom --no-owner --no-acl \
			--file=/export/omniv3_full.dump "$LEGACY_V3_DATABASE_URL"
	'

printf 'table,row_count\n' > "$OUTPUT_DIR/source_counts.csv"
printf 'table,status\n' > "$OUTPUT_DIR/export_manifest.csv"

for table in "${tables[@]}"; do
	if docker run --rm -e LEGACY_V3_DATABASE_URL "$POSTGRES_IMAGE" \
		psql "$LEGACY_V3_DATABASE_URL" -Atqc \
		"select 1 from information_schema.tables where table_schema='public' and table_name='$table'" \
		| grep -qx 1; then
		docker run --rm \
			-e LEGACY_V3_DATABASE_URL \
			-v "$OUTPUT_DIR:/export" \
			"$POSTGRES_IMAGE" \
			psql "$LEGACY_V3_DATABASE_URL" -v ON_ERROR_STOP=1 \
			-c "\\copy (select * from public.\"$table\") to '/export/${table}_rows.csv' with (format csv, header true)"
		count="$(docker run --rm -e LEGACY_V3_DATABASE_URL "$POSTGRES_IMAGE" \
			psql "$LEGACY_V3_DATABASE_URL" -Atqc "select count(*) from public.\"$table\"")"
		printf '%s,%s\n' "$table" "$count" >> "$OUTPUT_DIR/source_counts.csv"
		printf '%s,exported\n' "$table" >> "$OUTPUT_DIR/export_manifest.csv"
	else
		printf '%s,missing\n' "$table" >> "$OUTPUT_DIR/export_manifest.csv"
	fi
done

chmod 600 "$OUTPUT_DIR"/*
printf 'Export complete: %s\n' "$OUTPUT_DIR"
printf 'Review: %s\n' "$OUTPUT_DIR/export_manifest.csv"

