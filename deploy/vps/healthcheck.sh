#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${OMNIV4_ROOT:-/srv/omniv4}"
cd "$ROOT_DIR/app/deploy/vps"
set -a
. ./.env
set +a

notify_failure() {
	status=$?
	if [ -n "${HEALTHCHECK_WEBHOOK_URL:-}" ]; then
		curl --fail --silent --show-error --max-time 10 \
			--request POST \
			--header 'Content-Type: application/json' \
			--data "{\"status\":\"failed\",\"service\":\"Omni v4\",\"host\":\"$(hostname)\"}" \
			"$HEALTHCHECK_WEBHOOK_URL" >/dev/null || true
	fi
	exit "$status"
}
trap notify_failure ERR

required=(db redis-cache redis-queue backend frontend websocket queue-short queue-long scheduler proxy)
for service in "${required[@]}"; do
	container="$(docker compose --env-file .env ps -q "$service")"
	if [ -z "$container" ] || [ "$(docker inspect -f '{{.State.Running}}' "$container")" != "true" ]; then
		echo "CRITICAL: $service is not running" >&2
		exit 1
	fi
done

docker compose --env-file .env exec -T proxy \
	wget -qO- --header="Host: $FRAPPE_SITE_NAME" http://frontend:8080/api/method/ping \
	| grep -q '"pong"'

disk_used="$(df --output=pcent / | tail -n 1 | tr -dc '0-9')"
if [ "$disk_used" -ge 85 ]; then
	echo "CRITICAL: root filesystem is ${disk_used}% full" >&2
	exit 1
fi

echo "OK: all Omni services healthy; disk usage ${disk_used}%"
