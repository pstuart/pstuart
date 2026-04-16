#!/bin/bash
# Vue Anti-Pattern Guard — blocks forbidden CSS patterns in Vue files
# Enforces Tailwind-only styling

set -euo pipefail

input=$(cat)

tool_name=$(echo "$input" | jq -r '.tool_name // empty')

if [[ "$tool_name" != "Edit" && "$tool_name" != "Write" ]]; then
    exit 0
fi

new_string=$(echo "$input" | jq -r '.tool_input.new_string // .tool_input.content // empty')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

[[ -z "$new_string" ]] && exit 0
[[ -z "$file_path" ]] && exit 0

ext="${file_path##*.}"

# Only check Vue files
if [[ "$ext" != "vue" ]]; then
    exit 0
fi

if echo "$new_string" | grep -qE '<style\s+scoped'; then
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "reason": "Scoped styles are forbidden — use Tailwind CSS utility classes instead.\n\nReplace <style scoped> blocks with Tailwind classes in the template."
  },
  "continue": false
}
EOF
    exit 0
fi

if echo "$new_string" | grep -qE 'style="[^"]*"'; then
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "reason": "Inline styles are forbidden — use Tailwind CSS utility classes instead.\n\nReplace style=\"...\" with appropriate Tailwind classes."
  },
  "continue": false
}
EOF
    exit 0
fi

exit 0
