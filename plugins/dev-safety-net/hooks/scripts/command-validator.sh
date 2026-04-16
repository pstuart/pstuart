#!/bin/bash
# Command Validator — blocks dangerous commands and suggests safe alternatives
# Exit 0 = allow, outputs JSON with deny decision to block

set -euo pipefail

input=$(cat)

tool_name=$(echo "$input" | jq -r '.tool_name // empty')
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Only process Bash tool calls
if [[ "$tool_name" != "Bash" ]]; then
    exit 0
fi

# Block rm -rf and rm -r (dangerous recursive deletion)
if echo "$command" | grep -qE '\brm\s+(-[a-zA-Z]*r[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r|--recursive)\b'; then
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "reason": "rm -rf/rm -r is blocked for safety. Use 'trash' instead (brew install trash):\n  trash folder-name\n  trash file.txt\n\nThis moves items to Trash instead of permanent deletion."
  },
  "continue": false
}
EOF
    exit 0
fi

# Block git reset --hard (can lose uncommitted work)
if echo "$command" | grep -qE 'git\s+reset\s+--hard'; then
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "reason": "git reset --hard is blocked — it discards uncommitted changes permanently.\n\nSafer alternatives:\n  git stash         # Temporarily store changes\n  git checkout .    # Discard working tree changes (keeps staged)\n  git restore .     # Same as checkout ."
  },
  "continue": false
}
EOF
    exit 0
fi

# Block git push --force to main/master
if echo "$command" | grep -qE 'git\s+push\s+.*--force.*\s+(main|master)|git\s+push\s+.*-f.*\s+(main|master)'; then
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "reason": "Force push to main/master is blocked — this can destroy shared history.\n\nIf you really need this, run the command manually in terminal."
  },
  "continue": false
}
EOF
    exit 0
fi

# Allow all other commands
exit 0
