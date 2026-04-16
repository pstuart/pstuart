#!/bin/bash
# SwiftLint auto-format — runs swiftlint --fix after Swift file edits

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

if [[ "$ext" == "swift" ]]; then
    if command -v swiftlint &>/dev/null; then
        swiftlint --fix --path "$file_path" --quiet 2>/dev/null || true
    fi
fi

exit 0
