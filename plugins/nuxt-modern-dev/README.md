# nuxt-modern-dev

Modern Nuxt/Vue development toolkit for [Claude Code](https://claude.ai/code).

Enforces Tailwind-only styling, validates nginx configs, and provides web best practices.

## Install

```bash
claude plugin add pstuart/nuxt-modern-dev
```

## What It Does

### Anti-Pattern Guard (Hook)

Blocks forbidden styling patterns in Vue files:

| Blocked Pattern | Replacement |
|----------------|-------------|
| `<style scoped>` | Tailwind utility classes |
| `style="..."` inline styles | Tailwind utility classes |

### Auto-Format (Hook)

Runs `prettier --write` after every web file edit (.vue, .ts, .tsx, .js, .jsx, .css, .json).

### nginx Syntax Check (Hook)

Automatically runs `nginx -t` after editing `.conf` files that contain nginx directives.

### Skills

| Skill | Description |
|-------|-------------|
| Nuxt 4 Frontend | app/ directory, Composition API, Tailwind CSS 4, Vitest |
| Accessibility Audit | WCAG 2.1 AA compliance checklist |
| Security Audit | Web application security checklist |

## Requirements

- [jq](https://jqlang.org/) — for hook JSON processing
- [prettier](https://prettier.io/) — for auto-formatting (project-local)
- [nginx](https://nginx.org/) — optional, for config validation

## License

MIT
