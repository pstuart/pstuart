---
name: vue3-composition
description: Use when writing Vue 3 components or composables, choosing Options vs Composition API, handling reactivity, provide/inject, or script setup patterns.
---

# Vue 3 Composition API

**Baseline:** Vue 3 Composition API with `<script setup lang="ts">`. Confirm the exact Vue version from the repository lockfile.

## Non-negotiables

| ALWAYS | NEVER |
|--------|--------|
| `<script setup lang="ts">` for new components | Options API for new code |
| Composables named `useXxx`, return object | Return bare refs without naming |
| `readonly()` for state consumers must not mutate | Mutate props |
| Tailwind utilities for styling | Scoped CSS / inline styles (see `tailwindcss4`) |

## Decision tree

- Reusable stateful logic? → composable in `composables/useXxx.ts`
- Cross-tree dependency? → `provide` / `inject` with typed keys
- One-off UI state? → `ref` / `reactive` in the component
- Need Nuxt data fetching? → use `nuxt4-frontend` (`useFetch` / `useAsyncData`)

## Core patterns

```vue
<script setup lang="ts">
interface Props {
  title: string
  count?: number
}
const props = withDefaults(defineProps<Props>(), { count: 0 })
const emit = defineEmits<{ save: [id: string] }>()

const open = ref(false)
</script>

<template>
  <section class="space-y-2">
    <h2 class="text-lg font-semibold">{{ props.title }}</h2>
    <button class="rounded-lg bg-slate-900 px-3 py-2 text-white" @click="open = !open">
      Toggle
    </button>
  </section>
</template>
```

```ts
// composables/useToggle.ts
export function useToggle(initial = false) {
  const on = ref(initial)
  function toggle() {
    on.value = !on.value
  }
  return { on: readonly(on), toggle }
}
```

## Reactivity pitfalls

- Destructure `props` → lose reactivity unless `toRefs` / `storeToRefs`
- `reactive` + reassignment → prefer `ref` for reassignable state
- Async setup without `await` in Nuxt → prefer Nuxt async data APIs

## Load next

| When | Read |
|------|------|
| Nuxt-specific structure / data | `nuxt4-frontend` skill |
| Styling | `tailwindcss4` skill |

## Pre-finish checklist

- [ ] script setup + TS
- [ ] No prop mutation
- [ ] Composables return named object
- [ ] No Options API in new files
