#!/bin/bash
# nginx syntax check — validates nginx config after editing .conf files

set -euo pipefail

input=$(cat)
FILE_PATH=$(echo "$input" | jq -r '.tool_input.file_path // empty')

[[ -z "$FILE_PATH" ]] && exit 0
[[ "$FILE_PATH" != *.conf ]] && exit 0

# Only check if it looks like an nginx config
if grep -qE '^\s*(server|location|upstream|http|events)\s*\{' "$FILE_PATH" 2>/dev/null; then
    if ! nginx -t 2>&1; then
        echo ""
        echo "NGINX CONFIG ERROR — please fix before continuing"
        exit 1
    fi
fi

exit 0
