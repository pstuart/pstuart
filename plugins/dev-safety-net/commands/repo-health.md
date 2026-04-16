---
description: Scan all repos in a directory for health status — dirty files, sync state, open PRs, issues, merge conflicts, and branch hygiene
argument: Optional path to scan (defaults to ~/Development) or glob filter (e.g. "Better-*")
---

# Repo Health Report

Scan every git repo in the target directory and produce a consolidated health report.

## Step 1: Discover Repos

Find all git repos, optionally filtered by argument:

```bash
TARGET_DIR="${ARGUMENTS:-$HOME/Development}"

# If argument looks like a glob pattern, use ~/Development as base
if [[ "$TARGET_DIR" == *"*"* ]]; then
    cd ~/Development
    FILTER="$TARGET_DIR"
    TARGET_DIR="."
fi

repos=()
for dir in "$TARGET_DIR"/*/; do
    dir="${dir%/}"
    [ -d "$dir/.git" ] || continue
    if [ -n "${FILTER:-}" ]; then
        case "$(basename "$dir")" in $FILTER) ;; *) continue ;; esac
    fi
    repos+=("$dir")
done
echo "Found ${#repos[@]} repos to scan"
```

## Step 2: Scan Each Repo

For each repo, collect:
- Current branch
- Dirty state (modified/untracked files)
- Sync with upstream (ahead/behind/diverged)
- Open PRs (if gh CLI available)
- Open issues count

## Step 3: Compile Report

Organize into sections:
- **Summary** — X repos scanned, Y clean, Z need attention
- **Dirty Repos** — uncommitted changes with file lists
- **Out of Sync** — repos ahead/behind/diverged
- **Not on Default Branch** — repos on feature branches
- **Open PRs** — with mergeable status and review state
- **Open Issues** — counts and recent titles
- **Clean & Synced** — repos that are good

## Step 4: Recommendations

End with actionable items:
1. Auto-fixable (just needs git pull)
2. Needs commit (real changes)
3. Needs .gitignore (build artifacts tracked)
4. Needs merge/rebase (diverged)
5. PR attention (conflicts or stale reviews)
6. Branch cleanup (old feature branches)

Ask which actions the user wants to take.
