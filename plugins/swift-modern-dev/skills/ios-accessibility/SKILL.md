---
name: ios-accessibility
description: Use when implementing or auditing VoiceOver, Dynamic Type, accessibility labels, focus, contrast, or Hit-testing for SwiftUI iOS/macOS apps.
---

# iOS Accessibility

Ship usable apps with VoiceOver, Dynamic Type, and HIG accessibility baselines.

## Non-negotiables

| ALWAYS | NEVER |
|--------|--------|
| Meaningful `accessibilityLabel` on icon-only controls | Icon-only buttons with no label |
| Support Dynamic Type (no fixed tiny text) | Rely on color alone for meaning |
| ≥ ~44pt touch targets for interactive controls | Trap focus / unreadable contrast |
| Test with VoiceOver on critical flows | Ship decorative noise as accessibility elements |

## Decision tree

- Image/button without text? → label + optional hint
- Group of controls? → combine or container labels
- Custom control? → traits + value + actions
- Motion-heavy UI? → respect Reduce Motion

## Core patterns

```swift
Button {
    isFavorite.toggle()
} label: {
    Image(systemName: isFavorite ? "star.fill" : "star")
}
.accessibilityLabel(isFavorite ? "Remove from favorites" : "Add to favorites")
.accessibilityAddTraits(isFavorite ? .isSelected : [])

Text(title)
    .font(.body) // scales with Dynamic Type
    .accessibilityHeading(.h2)
```

```swift
.accessibilityElement(children: .combine)
.accessibilityAction(named: "Delete") { delete() }
```

## Checklist

- [ ] All interactive elements labeled
- [ ] Decorative images: `.accessibilityHidden(true)`
- [ ] Dynamic Type: no clipped essential text at largest sizes
- [ ] Contrast sufficient for text/icons
- [ ] VoiceOver order matches visual reading order

## Load next

| When | Read |
|------|------|
| Deep examples | Claude legacy examples under old skill if needed; prefer keep this slim |

## Pre-finish checklist

- [ ] Icon-only controls labeled
- [ ] VoiceOver path sanity-checked for the feature
