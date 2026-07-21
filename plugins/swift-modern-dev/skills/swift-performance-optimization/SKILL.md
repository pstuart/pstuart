---
name: swift-performance-optimization
description: Use when profiling slow SwiftUI screens, optimizing lists, reducing main-thread work, improving memory/CPU, or using Instruments Time Profiler or Swift Concurrency tools.
---

# Swift Performance Optimization

Profile first, then fix the measured hot path.

## Non-negotiables

| ALWAYS | NEVER |
|--------|--------|
| Measure with Instruments before large rewrites | Micro-optimize unmeasured code |
| Keep heavy work off `@MainActor` | Block main actor with parsing/image work |
| Prefer `@Observable` fine-grained updates | Force full-tree invalidation patterns |
| Use lazy stacks/grids for large collections | Eagerly build thousands of heavy subviews |

## Decision tree

- Jank while scrolling? → List/LazyVStack identity, row cost, images
- Hang on action? → Time Profiler; move work off main actor
- Memory climb? → `memory-leak-diagnosis` + Allocations
- Actor wait times? → Swift Concurrency instrument

## Core patterns

```swift
// Large lists: stable identity + light rows
List(items) { item in
    ItemRow(item: item) // small view, no heavy work in body
}
.listStyle(.plain)

// Background compute
actor Processor {
    func process(_ input: Data) async -> Result { /* heavy */ }
}

@MainActor
@Observable
final class VM {
    var result: Result?
    private let processor = Processor()

    func run(_ data: Data) async {
        result = await processor.process(data)
    }
}
```

```swift
// AsyncImage with phases; cache if product requires
AsyncImage(url: url) { phase in
    switch phase {
    case .success(let image): image.resizable().scaledToFill()
    case .failure: Image(systemName: "photo")
    default: ProgressView()
    }
}
```

## Instruments

1. Product → Profile → Time Profiler and/or Swift Concurrency
2. Invert call tree; watch main thread Self time
3. Fix top offenders only; re-measure

## Pre-finish checklist

- [ ] Bottleneck measured
- [ ] Main-actor work minimized
- [ ] Large collections use lazy containers
- [ ] Re-profiled or justified skip
