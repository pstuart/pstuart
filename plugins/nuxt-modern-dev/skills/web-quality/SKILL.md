---
name: web-quality
description: Use when setting up or running ESLint, Prettier, Vitest, or Playwright for Nuxt/Vue projects, deciding what to test, or enforcing pre-deploy quality gates.
---

# Web Quality (Lint, Format, Test)

**Baseline:** ESLint 9 with `@nuxt/eslint`, Vitest 4.x, and Playwright for critical E2E flows. Confirm versions from the repository lockfile.

## Non-negotiables

| ALWAYS | NEVER |
|--------|--------|
| ESLint with `@nuxt/eslint` on Nuxt apps | Skip lint because “types already catch it” |
| Prettier for format consistency | Hand-format only |
| Vitest for logic TypeScript cannot prove | Snapshot every presentational component |
| Playwright for critical user flows | E2E for every unit of logic |
| Fix or justify failures before deploy | Disable rules silently to green CI |

## Decision tree

- Pure function / composable logic / API handler? → **Vitest**
- Type-only guarantee? → **TypeScript**, no redundant test
- Login, checkout, deploy smoke? → **Playwright**
- Style debate? → **Prettier** (no bike-shedding)

## What to test (philosophy)

Tests encode **why** behavior matters:

- Do test: state transitions, edge cases, error paths, parsers, auth gates
- Don’t test: trivial getters, pure Tailwind class strings, framework wiring

## Core configs (minimal)

```ts
// eslint.config.mjs — prefer Nuxt module generated setup
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxt/eslint'],
})
```

```ts
// vitest — test composables/utils
import { describe, it, expect } from 'vitest'
import { formatCurrency } from '~/utils/money'

describe('formatCurrency', () => {
  it('formats USD', () => {
    expect(formatCurrency(12.5)).toMatch(/\$12\.50/)
  })
})
```

## Quick commands

```bash
bun run lint
bun run lint:fix
bun run typecheck
bun run test
bun run test:e2e   # if configured
bun run build      # required before deployment
```

## Pre-deploy gate

1. `bun run lint` clean
2. `bun run typecheck` clean
3. `bun run test` (unit)
4. `bun run build` succeeds
5. Smoke live URL after deploy

## Pre-finish checklist

- [ ] Lint/format scripts exist and run
- [ ] New logic has Vitest coverage or a clear “types-only” reason
- [ ] No eslint-disable without comment
