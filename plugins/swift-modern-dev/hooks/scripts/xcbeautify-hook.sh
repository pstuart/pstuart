#!/bin/bash
# xcbeautify hook — pipes xcodebuild output through xcbeautify for cleaner output

input=$(cat)

tool_name=$(echo "$input" | jq -r '.tool_name // empty')
command=$(echo "$input" | jq -r '.tool_input.command // empty')

if [[ "$tool_name" != "Bash" ]]; then
    exit 0
fi

if [[ "$command" == *"xcodebuild"* ]] && [[ "$command" != *"xcbeautify"* ]]; then
    if ! command -v xcbeautify &> /dev/null; then
        exit 0
    fi

    if [[ "$command" == *"set -o pipefail"* ]]; then
        new_command="${command} | xcbeautify"
    else
        new_command="set -o pipefail && NSUnbufferedIO=YES ${command} 2>&1 | xcbeautify"
    fi

    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "updatedInput": {
      "command": $(printf '%s' "$new_command" | jq -Rs .)
    }
  },
  "continue": true,
  "suppressOutput": false
}
EOF
    exit 0
fi

exit 0
