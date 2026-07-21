---
name: nuxt4-frontend
description: Use when building or reviewing Nuxt 4 apps, app/ directory layout, pages, layouts, server routes, composables, layers, or Nuxt data fetching.
---

# Nuxt 4 Frontend

**Baseline:** Nuxt 4.4.x, the `app/` directory, Tailwind 4, and strict TypeScript. Follow the repository's existing package manager and lockfile.

## Non-negotiables

| ALWAYS | NEVER |
|--------|--------|
| Put app code under `app/` | Root-level `pages/` / `components/` for new Nuxt 4 apps |
| Use the package manager selected by the repository | Introduce a second lockfile |
| Tailwind utilities only | Inline styles / `<style scoped>` |
| Type fetch results | Mock API payloads on failure |
| ESLint `@nuxt/eslint` | Ship without lint script |

## Project structure

```
app/
├── components/
├── composables/
├── utils/
├── types/
├── pages/
├── layouts/
├── middleware/
├── plugins/
└── assets/css/main.css
server/                 # API routes (root)
layers/                 # optional shared layers
nuxt.config.ts
```

## Decision tree

- Simple GET tied to route? → `useFetch`
- Complex key / transform / lazy? → `useAsyncData`
- Shared UI across sites? → Nuxt layer or a focused shared package
- Styling? → `tailwindcss4` skill
- Types? → `typescript-strict` skill
- Lint/test gates? → `web-quality` skill

## Core patterns

```vue
<script setup lang="ts">
const { data, error, pending } = await useFetch<Item[]>('/api/items')
</script>

<template>
  <div class="p-6">
    <p v-if="pending" class="text-slate-500">Loading…</p>
    <p v-else-if="error" class="text-red-600">Failed to load</p>
    <ul v-else class="space-y-2">
      <li v-for="item in data" :key="item.id" class="rounded-lg border p-3">
        {{ item.name }}
      </li>
    </ul>
  </div>
</template>
```

```ts
// server/api/items.get.ts
export default defineEventHandler(async () => {
  // real data source — no fake arrays for “happy path demos” in production code
  return await listItems()
})
```

## Quick commands

```bash
bun run dev
bun run typecheck
bun run lint
bun run lint:fix
bun run test
bun run build
```

## Load next

| When | Read |
|------|------|
| Vue component patterns | `vue3-composition` |
| CSS | `tailwindcss4` |
| ESLint / Vitest / Playwright | `web-quality` |
| Deploy failures | harness `deployment-doctor` (not this pack) |

## Common mistakes

| Excuse | Reality |
|--------|---------|
| "Pages at repo root is fine" | Nuxt 4 convention is `app/` |
| "I'll use a different package manager locally" | Match the checked-in lockfile and repository tooling |
| "Placeholder items for UI" | Use empty/error states |

## Pre-finish checklist

- [ ] Files under `app/` (or `server/`)
- [ ] Tailwind-only styling
- [ ] Typed data fetching; real error UI
- [ ] lint/typecheck considered
