---
name: ios-accessibility
description: Best practices for implementing accessibility features in iOS 17+ apps, including VoiceOver support, Dynamic Type, and Human Interface Guidelines compliance.
---

# iOS Accessibility Guide

## VoiceOver Support

```swift
Text("Submit")
    .accessibilityLabel("Submit form")
    .accessibilityHint("Double tap to send your message")
    .accessibilityAddTraits(.isButton)

// Group related elements
VStack {
    Text(item.title)
    Text(item.subtitle)
}
.accessibilityElement(children: .combine)

// Custom actions
.accessibilityAction(named: "Delete") {
    deleteItem()
}
```

## Dynamic Type

```swift
// Use ScaledMetric for custom sizes
@ScaledMetric var iconSize: CGFloat = 24
@ScaledMetric var spacing: CGFloat = 8

// Adapt layout for large text
@Environment(\.dynamicTypeSize) var typeSize

var body: some View {
    if typeSize >= .accessibility1 {
        VStack { content }  // Stack vertically for large text
    } else {
        HStack { content }  // Side by side for normal text
    }
}
```

## Reduce Motion

```swift
@Environment(\.accessibilityReduceMotion) var reduceMotion

var animation: Animation? {
    reduceMotion ? nil : .spring()
}
```

## Color Contrast

- Normal text: 4.5:1 minimum contrast ratio
- Large text (18pt+): 3:1 minimum
- UI components: 3:1 minimum
- Use semantic colors that adapt to light/dark mode

## Focus Management

```swift
@AccessibilityFocusState var focusedField: Field?

enum Field { case name, email, submit }

TextField("Name", text: $name)
    .accessibilityFocused($focusedField, equals: .name)

// Move focus programmatically
Button("Submit") {
    if name.isEmpty {
        focusedField = .name  // Focus the error field
    }
}
```
