#!/bin/bash
# Session Context — provides project context at session start

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

if ! git -C "$PROJECT_DIR" rev-parse --git-dir &>/dev/null; then
    exit 0
fi

cd "$PROJECT_DIR"

# Detect project type
PROJECT_TYPE="unknown"
if [[ -f "Package.swift" ]] || find . -maxdepth 2 -name "*.xcodeproj" -o -name "*.xcworkspace" 2>/dev/null | grep -q .; then
    PROJECT_TYPE="Swift/iOS"
elif [[ -f "nuxt.config.ts" ]] || [[ -f "nuxt.config.js" ]]; then
    PROJECT_TYPE="Nuxt"
elif [[ -f "package.json" ]]; then
    if grep -q '"vue"' package.json 2>/dev/null; then
        PROJECT_TYPE="Vue"
    elif grep -q '"next"' package.json 2>/dev/null; then
        PROJECT_TYPE="Next.js"
    else
        PROJECT_TYPE="Node.js"
    fi
elif [[ -f "Cargo.toml" ]]; then
    PROJECT_TYPE="Rust"
elif [[ -f "go.mod" ]]; then
    PROJECT_TYPE="Go"
elif [[ -f "requirements.txt" ]] || [[ -f "pyproject.toml" ]]; then
    PROJECT_TYPE="Python"
fi

# Find most recent plan
PLAN_CONTENT=""
if [[ -d "docs/plans" ]]; then
    RECENT_PLAN=$(find docs/plans -maxdepth 1 -name "*.md" -type f -exec ls -t {} + 2>/dev/null | head -1)
    if [[ -n "$RECENT_PLAN" && -f "$RECENT_PLAN" ]]; then
        PLAN_TITLE=$(grep -m1 "^# " "$RECENT_PLAN" 2>/dev/null | sed 's/^# //' || echo "$(basename "$RECENT_PLAN")")
        TOTAL_ITEMS=$(grep -c '^\s*- \[' "$RECENT_PLAN" 2>/dev/null || true)
        COMPLETED_ITEMS=$(grep -c '^\s*- \[x\]' "$RECENT_PLAN" 2>/dev/null || true)
        TOTAL_ITEMS=$((TOTAL_ITEMS + 0))
        COMPLETED_ITEMS=$((COMPLETED_ITEMS + 0))
        PENDING_ITEMS=$(grep '^\s*- \[ \]' "$RECENT_PLAN" 2>/dev/null | head -5 | sed 's/^\s*- \[ \] /  - /' || true)

        if [[ "$TOTAL_ITEMS" -gt 0 ]]; then
            PLAN_CONTENT="**Active Plan:** $PLAN_TITLE
**Progress:** $COMPLETED_ITEMS/$TOTAL_ITEMS items completed"
            if [[ -n "$PENDING_ITEMS" ]]; then
                PLAN_CONTENT+="
**Next items:**
$PENDING_ITEMS"
            fi
        fi
    fi
fi

# Git status
GIT_STATUS=""
UNCOMMITTED=$(git status --porcelain 2>/dev/null | head -10)
if [[ -n "$UNCOMMITTED" ]]; then
    MODIFIED_COUNT=$(echo "$UNCOMMITTED" | grep -c '^ M\|^M ' 2>/dev/null || true)
    ADDED_COUNT=$(echo "$UNCOMMITTED" | grep -c '^A \|^??' 2>/dev/null || true)
    DELETED_COUNT=$(echo "$UNCOMMITTED" | grep -c '^ D\|^D ' 2>/dev/null || true)
    MODIFIED_COUNT=$((MODIFIED_COUNT + 0))
    ADDED_COUNT=$((ADDED_COUNT + 0))
    DELETED_COUNT=$((DELETED_COUNT + 0))
    GIT_STATUS="$MODIFIED_COUNT modified, $ADDED_COUNT added, $DELETED_COUNT deleted
$(echo "$UNCOMMITTED" | head -5 | sed 's/^/  /')"
    TOTAL_CHANGES=$(echo "$UNCOMMITTED" | wc -l | tr -d '[:space:]')
    if [[ "$TOTAL_CHANGES" -gt 5 ]]; then
        GIT_STATUS+="
  ... and $((TOTAL_CHANGES - 5)) more files"
    fi
fi

# Recent commits
RECENT_COMMITS=""
COMMITS=$(git log --oneline -5 2>/dev/null || true)
if [[ -n "$COMMITS" ]]; then
    RECENT_COMMITS=$(echo "$COMMITS" | sed 's/^/  /')
fi

# Branch info
BRANCH_INFO=""
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "detached")
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
if [[ "$CURRENT_BRANCH" != "$DEFAULT_BRANCH" && "$CURRENT_BRANCH" != "detached" ]]; then
    AHEAD_BEHIND=$(git rev-list --left-right --count "$DEFAULT_BRANCH...$CURRENT_BRANCH" 2>/dev/null || echo "0 0")
    BEHIND=$(echo "$AHEAD_BEHIND" | awk '{print $1}')
    AHEAD=$(echo "$AHEAD_BEHIND" | awk '{print $2}')
    BRANCH_INFO="**Branch:** \`$CURRENT_BRANCH\` ($AHEAD ahead, $BEHIND behind \`$DEFAULT_BRANCH\`)"
fi

# Output
if [[ -n "$PLAN_CONTENT" || -n "$GIT_STATUS" ]]; then
    echo "# Session Context"
    echo ""
    echo "**Project:** $(basename "$PROJECT_DIR") ($PROJECT_TYPE)"
    if [[ -n "$BRANCH_INFO" ]]; then
        echo "$BRANCH_INFO"
    fi
    echo ""
    if [[ -n "$PLAN_CONTENT" ]]; then
        echo "## Current Plan"
        echo "$PLAN_CONTENT"
        echo ""
    fi
    if [[ -n "$GIT_STATUS" ]]; then
        echo "## Working Tree"
        echo "$GIT_STATUS"
        echo ""
    fi
    if [[ -n "$RECENT_COMMITS" ]]; then
        echo "## Recent Commits"
        echo "$RECENT_COMMITS"
        echo ""
    fi
fi

exit 0
