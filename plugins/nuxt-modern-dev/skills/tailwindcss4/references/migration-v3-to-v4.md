# Tailwind 3 → 4 migration for Nuxt apps

1. Remove `@nuxtjs/tailwindcss` from `modules` and dependencies.
2. Install `tailwindcss@^4` and `@tailwindcss/vite`.
3. Add Vite plugin in `nuxt.config.ts` (see SKILL.md).
4. Replace `tailwind.config.js` theme extensions with CSS `@theme { ... }`.
5. Point `css` at `app/assets/css/main.css` with `@import "tailwindcss"`.
6. Rename deprecated v3 utilities if build warns.
7. Delete obsolete PostCSS Tailwind plugins if unused.
8. `bun run build` and visual smoke test.
