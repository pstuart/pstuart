# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

This repository contains the GitHub profile README for `pstuart` and a public Claude Code plugin marketplace. The root `README.md` appears on [github.com/pstuart](https://github.com/pstuart).

## What's Here

- `README.md` — GitHub profile page (HTML/Markdown with badges, bio, project highlights, skills)
- `barista/README.md` — Redirect notice; Barista has moved to [github.com/pstuart/Barista](https://github.com/pstuart/Barista)
- `.claude-plugin/marketplace.json` — Claude Code marketplace catalog
- `plugins/` — Self-contained Claude Code plugins and their skills, hooks, and commands

## Notes for Claude

- Keep every marketplace plugin self-contained; installed plugins cannot depend on files outside their plugin directory
- Validate the marketplace and each plugin before publishing
- Changes to README.md are immediately reflected on the GitHub profile page after push to main
- Keep the README accurate: update skills, current projects, and featured work as needed
- Use badges from shields.io for consistent styling

## Validation

```bash
claude plugin validate .
for plugin in plugins/*; do
  claude plugin validate "$plugin"
done
```
