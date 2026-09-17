#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${OMNIV4_ROOT:-/srv/omniv4}"
DEPLOY_DIR="$ROOT_DIR/app/deploy/vps"
BACKUP_DIR="$ROOT_DIR/backups/encrypted"
KEY_FILE="$ROOT_DIR/secrets/backup.key"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

cd "$DEPLOY_DIR"
set -a
. ./.env
set +a

mkdir -p "$BACKUP_DIR" "$(dirname "$KEY_FILE")"
chmod 700 "$BACKUP_DIR" "$(dirname "$KEY_FILE")"
if [ ! -s "$KEY_FILE" ]; then
	umask 077
	openssl rand -hex 32 > "$KEY_FILE"
fi

container="$(docker compose --env-file .env ps -q backend)"
test -n "$container"
docker compose --env-file .env exec -T backend \
	bench --site "$FRAPPE_SITE_NAME" backup --with-files --compress

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT
docker cp "$container:/home/frappe/frappe-bench/sites/$FRAPPE_SITE_NAME/private/backups/." "$workdir/"
tar -C "$workdir" -czf - . | openssl enc -aes-256-cbc -pbkdf2 -salt \
	-pass "file:$KEY_FILE" -out "$BACKUP_DIR/$FRAPPE_SITE_NAME-$stamp.tar.gz.enc"
sha256sum "$BACKUP_DIR/$FRAPPE_SITE_NAME-$stamp.tar.gz.enc" \
	> "$BACKUP_DIR/$FRAPPE_SITE_NAME-$stamp.tar.gz.enc.sha256"

find "$BACKUP_DIR" -type f -mtime +"$RETENTION_DAYS" -delete

if [ -n "${BACKUP_REMOTE:-}" ] && command -v rclone >/dev/null 2>&1; then
	rclone copy "$BACKUP_DIR" "$BACKUP_REMOTE" --include '*.enc' --include '*.sha256'
fi

