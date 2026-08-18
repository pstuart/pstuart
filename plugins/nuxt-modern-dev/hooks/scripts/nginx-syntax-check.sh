#!/bin/bash
# nginx syntax check — validates a complete nginx config after editing .conf files.
# `nginx -t` without -c tests the live system config, which is unrelated to the
# file being edited. Snippets (server/location only) are not standalone configs.

set -euo pipefail

input=$(cat)
FILE_PATH=$(echo "$input" | jq -r '.tool_input.file_path // empty')

[[ -z "$FILE_PATH" ]] && exit 0
[[ "$FILE_PATH" != *.conf ]] && exit 0
[[ ! -f "$FILE_PATH" ]] && exit 0

if ! command -v nginx >/dev/null 2>&1; then
    exit 0
fi

# Require a full config (http or events). Do not test the live nginx.conf.
if ! grep -qE '^\s*(http|events)\s*\{' "$FILE_PATH" 2>/dev/null; then
    exit 0
fi

if ! nginx -t -c "$FILE_PATH" 2>&1; then
    echo ""
    echo "NGINX CONFIG ERROR in $FILE_PATH — please fix before continuing"
    exit 1
fi

exit 0
