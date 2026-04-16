---
name: accessibility-audit
description: Audit web pages and apps for WCAG 2.1 AA accessibility compliance. Use when fixing lighthouse issues, contrast ratios, ARIA labels, or keyboard navigation.
---

# Accessibility Audit

Comprehensive WCAG 2.1 AA compliance checklist for web applications.

## Quick Fixes for Common Issues

### Color Contrast (Most Common)

Minimum ratios:
- Normal text: 4.5:1
- Large text (18px+ or 14px bold): 3:1
- UI components: 3:1

Contrast-safe Tailwind pairs:

| Background | Text | Ratio |
|------------|------|-------|
| white | gray-700+ | 4.5:1+ |
| gray-100 | gray-800+ | 4.5:1+ |
| blue-600 | white | 4.5:1+ |
| red-700 | white | 4.5:1+ |

### Missing Language Attribute

```html
<html lang="en">
```

### Form Labels

```html
<label for="email">Email address</label>
<input id="email" type="email" aria-describedby="email-hint">
<span id="email-hint" class="text-sm text-gray-600">We'll never share your email</span>
```

### Keyboard Navigation

```html
<!-- Skip link -->
<a href="#main" class="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-white focus:p-4">
  Skip to main content
</a>

<!-- Focus styles (Tailwind) -->
<button class="focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
  Click me
</button>
```

### Image Alt Text

```html
<!-- Decorative -->
<img src="decoration.svg" alt="" role="presentation">

<!-- Informative -->
<img src="chart.png" alt="Sales increased 25% in Q4 2025">
```

## Full Audit Checklist

### Perceivable
- [ ] All images have alt text
- [ ] Videos have captions
- [ ] Semantic HTML structure
- [ ] Info not conveyed by color alone
- [ ] Text meets contrast ratios
- [ ] Readable at 200% zoom
- [ ] No horizontal scroll at 320px

### Operable
- [ ] All functionality keyboard accessible
- [ ] No keyboard traps
- [ ] Skip links present
- [ ] Descriptive page titles
- [ ] Logical tab order
- [ ] Focus indicators visible

### Understandable
- [ ] `<html lang="...">` present
- [ ] No unexpected context changes on focus
- [ ] Form errors clearly described
- [ ] All form inputs have labels

### Robust
- [ ] Valid HTML
- [ ] ARIA used correctly

## Vue/Nuxt Specific

```vue
<script setup lang="ts">
// Auto-announce route changes
const route = useRoute()
const announcer = ref('')

watch(() => route.path, () => {
  announcer.value = `Navigated to ${route.meta.title || route.path}`
})
</script>

<template>
  <div role="status" aria-live="polite" class="sr-only">
    {{ announcer }}
  </div>
</template>
```

## Testing

```bash
# Lighthouse CLI
npx lighthouse URL --only-categories=accessibility --output=json

# axe-core in tests
import axe from 'axe-core'
axe.run().then(results => console.log(results.violations))
```
