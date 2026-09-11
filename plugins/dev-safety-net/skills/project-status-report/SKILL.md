---
name: project-status-report
description: Generate comprehensive status reports for all projects in a folder. Use when asked for project rundowns, status reports, release readiness, or development summaries.
---
# Project status report

Report activity and readiness for the requested workspace. Inspect Git state and existing verification evidence first. Build or run checks only when the user requests current verification or it is needed for the agreed readiness assessment. Do not modify checkouts to make them appear clean or ready.

## Discover repositories

Use the requested workspace root as the working directory. This read-only discovery supports nested category directories and `.git` files used by linked worktrees; it prunes dependency/cache trees but does not assume a fixed depth:

```python
from pathlib import Path
import os
import subprocess

root = Path.cwd()
skip = {".git", "node_modules", ".build", ".swiftpm", ".venv", "venv", "DerivedData", "dist", "build", "archive"}
repositories = set()
for current, directories, files in os.walk(root):
    directories[:] = [name for name in directories if name not in skip]
    if not (Path(current) / ".git").exists():
        continue
    result = subprocess.run(
        ["git", "-C", current, "rev-parse", "--show-toplevel"],
        text=True, capture_output=True, check=False,
    )
    if result.returncode == 0:
        repositories.add(result.stdout.strip())
for repository in sorted(repositories):
    print(repository)
```

State discovery exclusions. For each exact repository root, inspect `git status --porcelain=v2`, current branch/HEAD, recent commits, and relevant existing build/test or release evidence. Report failed reads as unavailable; do not substitute an empty clean result.

## Verification when in scope

Read each repository's instructions and declared scripts. Use its package manager and supported build command. For Swift packages, use `swift build --package-path <repository>`. Xcode apps may need a documented project/scheme build instead. Do not introduce a new test file or helper without explicit authorization.

Preserve the command's exit code even when displaying a short log tail. For example, after choosing the correct working directory and command:

```python
from pathlib import Path
import subprocess

# Substitute the verified repository path and command for this project.
repository = Path("/absolute/path/to/project")
command = ["swift", "build", "--package-path", str(repository)]
result = subprocess.run(command, cwd=repository, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
print("\n".join(result.stdout.splitlines()[-20:]))
print(f"Build exit code: {result.returncode}")
raise SystemExit(result.returncode)
```

Run only checks relevant to the requested assessment; repeat after meaningful changes, failures, or unresolved concerns. Never infer a pass from a log tail or a pipeline's final command.

## Report

Give an overview and concise per-project results: exact checkout and revision, activity, existing changes, verification performed, failures or unavailable evidence, and actionable next steps. Distinguish implemented, locally validated, and externally released states. A clean tree or main branch alone does not prove release readiness, and an uncommitted reviewed change can still be implemented and locally validated.
