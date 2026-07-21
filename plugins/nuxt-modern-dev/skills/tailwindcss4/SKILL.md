---
name: tailwindcss4
description: Use when styling Nuxt or Vue UI, migrating from Tailwind 3, configuring @tailwindcss/vite, writing utility classes, or tempted to add custom CSS or inline styles.
---

# Tailwind CSS 4

**Baseline:** Tailwind 4.x via `@tailwindcss/vite`. Confirm the exact version from the repository lockfile.

## Non-negotiables

| ALWAYS | NEVER |
|--------|--------|
| Utility classes in templates | `style="..."` or `:style` for layout/color/spacing |
| `@tailwindcss/vite` plugin | `@nuxtjs/tailwindcss` module (v3 path) |
| CSS `@theme` for design tokens | New `tailwind.config.js` as primary config |
| Extract repeated UI to components | Large `@apply` blocks as a style system |
| Responsive + state variants (`md:`, `hover:`) | `<style scoped>` for anything Tailwind can do |

**Violating the letter of the Tailwind-only rule is violating the spirit.** Hooks may block scoped/inline styles; skills still teach the judgment call.

## Decision tree

- Need spacing/color/type? → Tailwind utilities on the element
- Same class cluster 3+ times? → Component, not `@apply` soup
- Need brand tokens? → `@theme` in `app/assets/css/main.css`
- Migrating v3 project? → `references/migration-v3-to-v4.md`

## Core setup (Nuxt 4)

```ts
// nuxt.config.ts
import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  vite: { plugins: [tailwindcss()] },
  css: ['~/assets/css/main.css'],
})
```

```css
/* app/assets/css/main.css */
@import "tailwindcss";

@theme {
  --color-brand: #2563eb;
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
}
```

```vue
<!-- good -->
<button class="rounded-xl bg-blue-600 px-6 py-3 text-white hover:bg-blue-700">
  Submit
</button>
```

```vue
<!-- bad -->
<button style="padding: 12px">Submit</button>
<style scoped>
.btn { padding: 12px; }
</style>
```

## Quick commands

```bash
bun add -d tailwindcss @tailwindcss/vite
# remove legacy: @nuxtjs/tailwindcss, tailwind.config.js (after migration)
```

## Load next

| When | Read |
|------|------|
| Migrating from Tailwind 3 | `references/migration-v3-to-v4.md` |

## Common mistakes

| Excuse | Reality |
|--------|---------|
| "Just one scoped style" | Becomes many; use utilities or a component |
| "Need arbitrary values always" | Prefer theme tokens; arbitrary is escape hatch |
| "v3 config still works fine" | New apps and migrations use v4 CSS-first path |

## Pre-finish checklist

- [ ] No inline styles / scoped CSS for Tailwind-expressible rules
- [ ] Using `@tailwindcss/vite`, not Nuxt Tailwind module
- [ ] Tokens in `@theme` when brand-specific
