#!/bin/bash
# Project Task List — ensures each project has a unique task list ID

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

if [[ ! -d "$PROJECT_DIR" ]]; then
    exit 0
fi

CLAUDE_DIR="$PROJECT_DIR/.claude"
LOCAL_SETTINGS="$CLAUDE_DIR/settings.local.json"

mkdir -p "$CLAUDE_DIR"

if [[ -f "$LOCAL_SETTINGS" ]]; then
    EXISTING_ID=$(jq -r '.env.CLAUDE_CODE_TASK_LIST_ID // empty' "$LOCAL_SETTINGS" 2>/dev/null || true)
    if [[ -n "$EXISTING_ID" ]]; then
        exit 0
    fi
    TASK_LIST_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
    jq --arg id "$TASK_LIST_ID" '
        if .env then
            .env.CLAUDE_CODE_TASK_LIST_ID = $id
        else
            .env = { "CLAUDE_CODE_TASK_LIST_ID": $id }
        end
    ' "$LOCAL_SETTINGS" > "${LOCAL_SETTINGS}.tmp" && mv "${LOCAL_SETTINGS}.tmp" "$LOCAL_SETTINGS"
else
    TASK_LIST_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
    cat > "$LOCAL_SETTINGS" << EOF
{
  "env": {
    "CLAUDE_CODE_TASK_LIST_ID": "$TASK_LIST_ID"
  }
}
EOF
fi

if git -C "$PROJECT_DIR" rev-parse --git-dir &>/dev/null; then
    GITIGNORE="$PROJECT_DIR/.gitignore"
    if [[ -f "$GITIGNORE" ]]; then
        if ! grep -q "\.claude/settings\.local\.json" "$GITIGNORE" 2>/dev/null; then
            echo "" >> "$GITIGNORE"
            echo "# Claude Code local settings (not shared)" >> "$GITIGNORE"
            echo ".claude/settings.local.json" >> "$GITIGNORE"
        fi
    fi
fi

exit 0
