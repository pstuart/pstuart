#!/bin/bash
# Prettier auto-format — runs prettier after web file edits

set -euo pipefail

input=$(cat)

tool_name=$(echo "$input" | jq -r '.tool_name // empty')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [[ "$tool_name" != "Edit" && "$tool_name" != "Write" ]]; then
    exit 0
fi

[[ -z "$file_path" ]] && exit 0
[[ ! -f "$file_path" ]] && exit 0

ext="${file_path##*.}"

case "$ext" in
    vue|ts|tsx|js|jsx|css|json)
        project_dir=$(dirname "$file_path")
        while [[ "$project_dir" != "/" ]]; do
            if [[ -f "$project_dir/node_modules/.bin/prettier" ]]; then
                "$project_dir/node_modules/.bin/prettier" --write "$file_path" 2>/dev/null || true
                break
            fi
            project_dir=$(dirname "$project_dir")
        done
        ;;
esac

exit 0
