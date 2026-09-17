#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${OMNIV4_ROOT:-/srv/omniv4}"
DEPLOY_DIR="$ROOT_DIR/app/deploy/vps"
BACKUP_DIR="$ROOT_DIR/backups/encrypted"
KEY_FILE="$ROOT_DIR/secrets/backup.key"

cd "$DEPLOY_DIR"
set -a
. ./.env
set +a

backup="${1:-$(find "$BACKUP_DIR" -maxdepth 1 -name '*.tar.gz.enc' -type f | sort | tail -n 1)}"
if [ -z "$backup" ] || [ ! -f "$backup" ]; then
	echo "No encrypted backup found" >&2
	exit 1
fi

checksum="$backup.sha256"
test -s "$KEY_FILE"
test -s "$checksum"
(cd "$(dirname "$backup")" && sha256sum -c "$(basename "$checksum")")

workdir="$(mktemp -d)"
database="omni_restore_drill_$(date -u +%Y%m%d%H%M%S)"
cleanup() {
	docker compose --env-file .env exec -T db env MYSQL_PWD="$MARIADB_ROOT_PASSWORD" \
		mariadb -uroot -e "DROP DATABASE IF EXISTS \`$database\`;" >/dev/null 2>&1 || true
	rm -rf "$workdir"
}
trap cleanup EXIT

openssl enc -d -aes-256-cbc -pbkdf2 \
	-pass "file:$KEY_FILE" -in "$backup" | tar -C "$workdir" -xzf -

sql_backup="$(find "$workdir" -type f -name '*database.sql.gz' | sort | tail -n 1)"
if [ -z "$sql_backup" ]; then
	echo "Backup does not contain a database dump" >&2
	exit 1
fi

while IFS= read -r archive; do
	tar -tzf "$archive" >/dev/null
done < <(find "$workdir" -type f \( -name '*files.tar.gz' -o -name '*private-files.tar.gz' \))

docker compose --env-file .env exec -T db env MYSQL_PWD="$MARIADB_ROOT_PASSWORD" \
	mariadb -uroot -e "CREATE DATABASE \`$database\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
gzip -dc "$sql_backup" | docker compose --env-file .env exec -T db \
	env MYSQL_PWD="$MARIADB_ROOT_PASSWORD" mariadb -uroot "$database"

doctype_count="$(docker compose --env-file .env exec -T db env MYSQL_PWD="$MARIADB_ROOT_PASSWORD" \
	mariadb -uroot --batch --skip-column-names "$database" \
	-e 'SELECT COUNT(*) FROM `tabDocType`;')"
administrator_count="$(docker compose --env-file .env exec -T db env MYSQL_PWD="$MARIADB_ROOT_PASSWORD" \
	mariadb -uroot --batch --skip-column-names "$database" \
	-e 'SELECT COUNT(*) FROM `tabUser` WHERE name = "Administrator";')"

if [ "$doctype_count" -lt 1 ] || [ "$administrator_count" -ne 1 ]; then
	echo "Restore validation failed" >&2
	exit 1
fi

echo "OK: restored $(basename "$backup") into an isolated database (${doctype_count} DocTypes)"
