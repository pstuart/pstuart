# dev-safety-net

Universal developer safety guardrails for [Claude Code](https://claude.ai/code).

## What It Does

Protects you from common mistakes and keeps your workflow informed:

- **Command Validator** — blocks `rm -rf`, `git reset --hard`, and force-push to main/master
- **Auto-Format** — runs swiftlint/prettier after every file edit
- **Build Check** — verifies your project builds before ending a session
- **Session Context** — shows project type, active plan, git status, and recent commits at session start
- **Project Task List** — isolates task lists per project so they don't bleed across repos
- **Repo Health** — scan all repos for dirty state, sync issues, and open PRs

## Install

```bash
claude plugin add pstuart/dev-safety-net
```

## Components

### Hooks

| Hook | Event | What It Does |
|------|-------|-------------|
| Command Validator | PreToolUse:Bash | Blocks dangerous commands, suggests safe alternatives |
| Auto-Format | PostToolUse:Edit\|Write | Runs swiftlint --fix / prettier --write after edits |
| Session Context | SessionStart | Shows project info, plan progress, git status |
| Project Task List | SessionStart | Creates per-project task list IDs |
| Build Check | Stop | Verifies build succeeds before session ends |

### Commands

| Command | Description |
|---------|-------------|
| `/repo-health` | Scan repos for dirty files, sync state, open PRs |

### Skills

| Skill | Description |
|-------|-------------|
| Project Status Report | Generate multi-project status reports |

## Requirements

- [jq](https://jqlang.org/) — for JSON processing in hooks
- [trash](https://formulae.brew.sh/formula/trash) — recommended safe alternative to rm
- [swiftlint](https://github.com/realm/SwiftLint) — optional, for Swift auto-formatting
- [prettier](https://prettier.io/) — optional, for web file auto-formatting

## License

MIT
