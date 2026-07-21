# nuxt-modern-dev

Modern Nuxt/Vue development toolkit for [Claude Code](https://claude.ai/code).

Enforces Tailwind-only styling, validates nginx configs, and provides web best practices.

## Install

```bash
/plugin marketplace add pstuart/pstuart
/plugin install nuxt-modern-dev@pstuart
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
| Nuxt 4 Frontend | `app/` directory, data fetching, layers, and project structure |
| Tailwind CSS 4 | Vite integration, theme tokens, utilities, and migration guidance |
| TypeScript Strict | Strict typing for components, composables, and API responses |
| Vue 3 Composition | `<script setup>`, reactivity, composables, and provide/inject |
| Web Quality | ESLint, Prettier, Vitest, Playwright, and deployment gates |
| Accessibility Audit | WCAG 2.1 AA compliance checklist |
| Security Audit | Web application security checklist |

## Requirements

- [jq](https://jqlang.org/) — for hook JSON processing
- [prettier](https://prettier.io/) — for auto-formatting (project-local)
- [nginx](https://nginx.org/) — optional, for config validation

## License

MIT
