---
name: nuxt4-frontend
description: Expert guidance for Nuxt 4 projects with app/ directory structure, Vue 3 Composition API, TypeScript, Vitest, ESLint, and Tailwind CSS 4. Use when creating components, composables, tests, or any frontend code.
---

# Nuxt 4 Frontend Guide

## Project Structure

```
app/
  components/       # Auto-imported Vue components
  composables/      # Auto-imported composables (use*.ts)
  layouts/          # Layout components
  middleware/       # Route middleware
  pages/            # File-based routing
  plugins/          # Nuxt plugins
  utils/            # Auto-imported utility functions
server/
  api/              # Server API routes
  middleware/       # Server middleware
  utils/            # Server utilities
public/             # Static assets
```

## Component Pattern

```vue
<script setup lang="ts">
interface Props {
  title: string
  items: Item[]
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
})

const emit = defineEmits<{
  select: [item: Item]
  delete: [id: string]
}>()
</script>

<template>
  <div class="rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800">
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
      {{ title }}
    </h2>
    <div v-if="isLoading" class="flex items-center justify-center py-8">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
    </div>
    <ul v-else class="mt-4 divide-y divide-gray-200 dark:divide-gray-700">
      <li
        v-for="item in items"
        :key="item.id"
        class="cursor-pointer px-2 py-3 transition-colors hover:bg-gray-50 dark:hover:bg-gray-700"
        @click="emit('select', item)"
      >
        {{ item.name }}
      </li>
    </ul>
  </div>
</template>
```

## Composable Pattern

```typescript
// composables/useItems.ts
export function useItems() {
  const items = ref<Item[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchItems() {
    isLoading.value = true
    error.value = null
    try {
      const data = await $fetch<Item[]>('/api/items')
      items.value = data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch items'
    } finally {
      isLoading.value = false
    }
  }

  return { items, isLoading, error, fetchItems }
}
```

## Server API Pattern

```typescript
// server/api/items/[id].get.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) {
    throw createError({ statusCode: 400, message: 'Missing item ID' })
  }

  const item = await getItemById(id)
  if (!item) {
    throw createError({ statusCode: 404, message: 'Item not found' })
  }

  return item
})
```

## Tailwind CSS 4

Tailwind 4 uses CSS-based configuration via `@tailwindcss/vite`:

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  css: ['~/assets/css/main.css'],
  vite: {
    plugins: [tailwindcss()],
  },
})
```

```css
/* assets/css/main.css */
@import 'tailwindcss';

@theme {
  --color-primary: #3b82f6;
  --color-primary-dark: #2563eb;
}
```

## Testing with Vitest

```typescript
// tests/composables/useItems.test.ts
import { describe, it, expect, vi } from 'vitest'
import { useItems } from '~/composables/useItems'

describe('useItems', () => {
  it('fetches items successfully', async () => {
    vi.stubGlobal('$fetch', vi.fn().mockResolvedValue([
      { id: '1', name: 'Item 1' },
    ]))

    const { items, fetchItems, isLoading } = useItems()
    await fetchItems()

    expect(items.value).toHaveLength(1)
    expect(isLoading.value).toBe(false)
  })
})
```

## Rules

- **Tailwind only** — no `<style>` blocks, no inline styles
- **TypeScript strict** — no `any` types
- **Composition API** — always `<script setup lang="ts">`
- **Auto-imports** — don't manually import Vue/Nuxt composables
- **$fetch** — use Nuxt's `$fetch` instead of raw `fetch`
