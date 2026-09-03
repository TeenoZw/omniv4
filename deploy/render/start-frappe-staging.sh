#!/usr/bin/env bash
set -euo pipefail

cd /home/frappe/frappe-bench

SITE_NAME="${FRAPPE_SITE_NAME:-admin-v4.omnilogistics.co.zw}"
DB_HOST="${DB_HOST:-omniv4-mariadb}"
DB_PORT="${DB_PORT:-3306}"
REDIS_CACHE="${REDIS_CACHE:-redis://omniv4-redis:6379}"
REDIS_QUEUE="${REDIS_QUEUE:-redis://omniv4-redis:6379}"
SOCKETIO_PORT="${SOCKETIO_PORT:-9000}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:?MYSQL_ROOT_PASSWORD is required}"

wait_for_tcp() {
	local host="$1"
	local port="$2"
	local label="$3"
	local attempt=0

	until timeout 2 bash -c "cat < /dev/null > /dev/tcp/${host}/${port}" 2>/dev/null; do
		attempt=$((attempt + 1))
		if [ "$attempt" -gt 60 ]; then
			echo "Timed out waiting for ${label} at ${host}:${port}" >&2
			exit 1
		fi
		sleep 2
	done
}

wait_for_tcp "$DB_HOST" "$DB_PORT" "MariaDB"

bench set-config -g db_host "$DB_HOST"
bench set-config -gp db_port "$DB_PORT"
bench set-config -g redis_cache "$REDIS_CACHE"
bench set-config -g redis_queue "$REDIS_QUEUE"
bench set-config -g redis_socketio "$REDIS_QUEUE"
bench set-config -gp socketio_port "$SOCKETIO_PORT"
printf "frappe\nerpnext\nomni_operations\n" > sites/apps.txt

if [ ! -d "sites/${SITE_NAME}" ]; then
	bench new-site "$SITE_NAME" \
		--mariadb-user-host-login-scope='%' \
		--admin-password="$ADMIN_PASSWORD" \
		--db-root-username="${DB_ROOT_USER:-root}" \
		--db-root-password="$MYSQL_ROOT_PASSWORD" \
		--install-app erpnext \
		--set-default

	bench --site "$SITE_NAME" install-app omni_operations
else
	bench --site "$SITE_NAME" migrate
fi

bench use "$SITE_NAME"
bench --site "$SITE_NAME" enable-scheduler || true

bench schedule &
bench worker --queue short,default,long &
node apps/frappe/socketio.js &

exec /home/frappe/frappe-bench/env/bin/gunicorn \
	--chdir=/home/frappe/frappe-bench/sites \
	--bind=0.0.0.0:${PORT:-8000} \
	--threads="${GUNICORN_THREADS:-4}" \
	--workers="${GUNICORN_WORKERS:-2}" \
	--worker-class=gthread \
	--worker-tmp-dir=/dev/shm \
	--timeout="${GUNICORN_TIMEOUT:-120}" \
	--preload \
	frappe.app:application
