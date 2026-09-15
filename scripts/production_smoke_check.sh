#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-${OMNI_ADMIN_URL:-}}"

if [ -z "$BASE_URL" ]; then
	echo "Usage: scripts/production_smoke_check.sh https://admin-v4.omnilogistics.co.zw" >&2
	exit 64
fi

BASE_URL="${BASE_URL%/}"

check_url() {
	local label="$1"
	local path="$2"
	local expected="${3:-200}"
	local status

	status="$(curl -k -sS -o /dev/null -w '%{http_code}' "${BASE_URL}${path}")"
	if [ "$status" != "$expected" ]; then
		echo "FAIL ${label}: expected HTTP ${expected}, got ${status}" >&2
		exit 1
	fi
	echo "OK ${label}: HTTP ${status}"
}

check_url "Frappe ping" "/api/method/ping" "200"
check_url "Login page" "/login" "200"

echo "Smoke checks passed for ${BASE_URL}"
