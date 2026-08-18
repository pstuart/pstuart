# No GitHub Actions

This repository does **not** use GitHub Actions for CI, tests, lint, deploy, or releases.

It is a GitHub profile README plus a public Claude Code plugin marketplace. Run validation and tests locally:

```bash
claude plugin validate . --strict
for plugin in plugins/*; do
  claude plugin validate "$plugin" --strict
done

# book-publisher engine
cd plugins/pstuart-publishing/skills/book-publisher
python3 -m pytest -q
```

Do not add `.github/workflows/*.yml`.
