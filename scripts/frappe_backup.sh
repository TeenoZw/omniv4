#!/usr/bin/env bash
set -euo pipefail

SITE="${FRAPPE_SITE_NAME:-admin-v4.omnilogistics.co.zw}"
CONTAINER="${FRAPPE_CONTAINER:-omniv4-frappe}"
BACKUP_DIR="${BACKUP_DIR:-./backups/frappe}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

mkdir -p "$BACKUP_DIR"

echo "Creating Frappe backup for ${SITE} from container ${CONTAINER}..."
docker exec "$CONTAINER" bash -lc "cd /home/frappe/frappe-bench && bench --site '${SITE}' backup --with-files"

STAMP="$(date +%Y%m%d-%H%M%S)"
TARGET="${BACKUP_DIR}/${SITE}-${STAMP}"
mkdir -p "$TARGET"

docker cp "${CONTAINER}:/home/frappe/frappe-bench/sites/${SITE}/private/backups/." "$TARGET/"

find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -mtime +"$RETENTION_DAYS" -print -exec rm -rf {} +

echo "Backup copied to ${TARGET}"
