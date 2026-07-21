---
name: typescript-strict
description: Use when writing or reviewing TypeScript in Vue, Nuxt, Node, or shared TS utilities, fixing type errors, or deciding how to type API responses and composables.
---

# TypeScript Strict

**Baseline:** TypeScript strict mode. Confirm the exact compiler version from the repository lockfile.

## Non-negotiables

| ALWAYS | NEVER |
|--------|--------|
| `strict: true` in tsconfig | `any` (use `unknown` + narrow) |
| Type props, emits, composable returns | Silence errors with `@ts-ignore` / blanket `as any` |
| Type `useFetch` / API data | Fake/mock data when the real API fails |
| Prefer `interface`/`type` for shared shapes | Implicit `any` parameters |

## Decision tree

- Value from outside world (JSON, query)? → `unknown` then narrow, or zod/schema if project already uses it
- Composable state? → Explicit return type object
- Vue props? → `defineProps<{ ... }>()` typed
- Error values? → `unknown` in `catch`, narrow before use

## Core patterns

```ts
// composable return — named fields, readonly state
export function useCounter(initial = 0) {
  const count = ref(initial)
  function inc() {
    count.value++
  }
  return { count: readonly(count), inc }
}

// fetch — type the data, handle error state (no mock fallback)
const { data, error, pending } = await useFetch<Item[]>('/api/items')
if (error.value) {
  // show error UI — do not invent items
}
```

```ts
// bad
function parse(x: any) {
  return x.foo
}

// good
function parse(x: unknown): string {
  if (typeof x === 'object' && x && 'foo' in x && typeof (x as { foo: unknown }).foo === 'string') {
    return (x as { foo: string }).foo
  }
  throw new Error('Invalid payload')
}
```

## Quick commands

```bash
bun run typecheck
# or
nuxi typecheck
```

## Common mistakes

| Excuse | Reality |
|--------|---------|
| "any is faster" | Breaks refactors; use `unknown` |
| "I'll fix types later" | Later never; type at the boundary now |
| "Mock data if API fails" | Forbidden — show error state |

## Pre-finish checklist

- [ ] No new `any` / `@ts-ignore`
- [ ] External data typed or narrowed
- [ ] `typecheck` considered or run
