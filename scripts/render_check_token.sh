#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -gt 1 ]; then
	echo "Usage: scripts/render_check_token.sh [/absolute/path/to/render-token-or-env-file]" >&2
	exit 64
fi

TOKEN_FILE="${1:-}"
TOKEN="${RENDER_API_TOKEN:-}"

if [ -n "$TOKEN_FILE" ]; then
	if [ ! -f "$TOKEN_FILE" ]; then
		echo "Render token file not found: $TOKEN_FILE" >&2
		exit 66
	fi

	if grep -q '^RENDER_API_TOKEN=' "$TOKEN_FILE"; then
		TOKEN="$(python3 - "$TOKEN_FILE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
value = ""
for line in path.read_text().splitlines():
    if line.startswith("RENDER_API_TOKEN="):
        value = line.split("=", 1)[1].strip().strip("\"'")
print(value.strip())
PY
)"
	else
		TOKEN="$(tr -d '\r\n[:space:]' < "$TOKEN_FILE")"
	fi
fi

if [ -z "$TOKEN" ]; then
	echo "Render token is empty. Set RENDER_API_TOKEN or pass a token/env file path." >&2
	exit 65
fi

curl -fsS \
	-H "Accept: application/json" \
	-H "Authorization: Bearer ${TOKEN}" \
	"https://api.render.com/v1/owners" \
	| python3 -c '
import json
import sys

payload = json.load(sys.stdin)
owners = []
for item in payload:
    owner = item.get("owner", item)
    owners.append({
        "id": owner.get("id"),
        "name": owner.get("name"),
        "type": owner.get("type"),
    })
print(json.dumps({"ok": True, "owners": owners}, indent=2))
'
