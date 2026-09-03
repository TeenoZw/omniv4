#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
	echo "Usage: scripts/render_check_token.sh /absolute/path/to/render-token-file" >&2
	exit 64
fi

TOKEN_FILE="$1"

if [ ! -f "$TOKEN_FILE" ]; then
	echo "Render token file not found: $TOKEN_FILE" >&2
	exit 66
fi

TOKEN="$(tr -d '\r\n[:space:]' < "$TOKEN_FILE")"

if [ -z "$TOKEN" ]; then
	echo "Render token file is empty." >&2
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
