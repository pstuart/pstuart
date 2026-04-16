---
name: project-status-report
description: Generate comprehensive status reports for all projects in a folder. Use when asked for project rundowns, status reports, release readiness, or development summaries.
---

# Project Status Report Generator

Generate comprehensive markdown reports on project status, development activity, and release readiness.

## When to Use

- "Give me a report of all projects"
- "What's the status of projects in this folder?"
- "Which projects are release ready?"
- "Show me development activity"

## Report Generation Process

### Step 1: Discover Projects

```bash
# Find all projects with git repos
find . -maxdepth 2 -name ".git" -type d | while read git; do
  dirname "$git"
done
```

### Step 2: Gather Metrics Per Project

For each project, collect:

```bash
PROJECT="./project-name"

# Git activity
git -C "$PROJECT" log --oneline -5 2>/dev/null
git -C "$PROJECT" log --since="7 days ago" --oneline 2>/dev/null | wc -l

# Uncommitted changes
git -C "$PROJECT" status --porcelain 2>/dev/null | wc -l

# Last commit date
git -C "$PROJECT" log -1 --format="%cr" 2>/dev/null

# Branch info
git -C "$PROJECT" branch --show-current 2>/dev/null

# Build status (try to build)
if [[ -f "$PROJECT/Package.swift" ]]; then
  swift build -C "$PROJECT" 2>&1 | tail -1
elif [[ -f "$PROJECT/package.json" ]]; then
  (cd "$PROJECT" && npm run build 2>&1 | tail -1)
fi
```

### Step 3: Determine Release Readiness

Check:
- [ ] Builds without errors
- [ ] Tests pass
- [ ] No uncommitted changes
- [ ] On main/master branch
- [ ] Version number updated

### Step 4: Generate Report

Present a markdown report with:
- Summary table (total projects, release ready, active, needs attention)
- Per-project details (type, branch, last activity, build/test status)
- Recent commits per project
- Outstanding work items
- Recommendations for next actions
