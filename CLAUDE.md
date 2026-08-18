# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

This repository contains the GitHub profile README for `pstuart` and a public Claude Code plugin marketplace. The root `README.md` appears on [github.com/pstuart](https://github.com/pstuart).

GitHub Issues are disabled on this profile repository. Propose work with pull requests.

## What's Here

- `README.md` — GitHub profile page (HTML/Markdown with badges, bio, project highlights, skills)
- `barista/README.md` — Redirect notice; Barista has moved to [github.com/pstuart/Barista](https://github.com/pstuart/Barista)
- `.claude-plugin/marketplace.json` — Claude Code marketplace catalog
- `plugins/` — Self-contained Claude Code plugins and their skills, hooks, and commands
  - `dev-safety-net` — command guardrails, format/build hooks, repo health
  - `swift-modern-dev` — Swift/SwiftUI architecture, anti-pattern hooks, `/package-dmg`
  - `nuxt-modern-dev` — Nuxt 4 / Vue 3 / Tailwind 4 skills and Vue style hooks
  - `pstuart-publishing` — book-publisher skill (PDF/EPUB/covers)

## Notes for Claude

- Keep every marketplace plugin self-contained; installed plugins cannot depend on files outside their plugin directory
- Validate the marketplace and each plugin before publishing
- Changes to README.md are immediately reflected on the GitHub profile page after push to main
- Keep the README accurate: update skills, current projects, featured work, star counts, and the blog list as needed
- Use badges from shields.io for consistent styling
- Do not commit `.claude/settings.local.json` (ignored via `.claude/`)
- Plugin hook commands must quote `"${CLAUDE_PLUGIN_ROOT}"` so install paths with spaces work

## Validation

```bash
claude plugin validate . --strict
for plugin in plugins/*; do
  claude plugin validate "$plugin" --strict
done

# book-publisher engine (optional extras: poppler, epubcheck)
cd plugins/pstuart-publishing/skills/book-publisher
python3 -m pytest -q
```
