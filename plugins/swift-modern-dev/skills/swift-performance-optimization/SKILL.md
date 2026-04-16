---
name: swift-performance-optimization
description: Techniques for optimizing Swift code performance, memory usage, rendering efficiency, and using Instruments for profiling.
---

# Swift Performance Optimization

## Instruments Profiling

### Memory Leaks
1. Open Instruments > Leaks template
2. Run the app and exercise key flows
3. Look for leak indicators (red bars)
4. Examine backtrace to find retain cycles

### Time Profiler
1. Instruments > Time Profiler
2. Focus on main thread hangs (>16ms for 60fps)
3. Sort by self weight to find hot paths
4. Use `signpost` for custom intervals

### Common Fixes

**Retain Cycles in Closures:**
```swift
// Problem
service.onComplete = { 
    self.update()  // strong capture
}

// Fix
service.onComplete = { [weak self] in
    self?.update()
}
```

**Lazy Collections:**
```swift
// Eager (allocates full array)
let results = items.filter { $0.isValid }.map { $0.name }

// Lazy (processes on demand)
let results = items.lazy.filter { $0.isValid }.map { $0.name }
```

**@MainActor Isolation:**
```swift
// Instead of dispatching to main queue
@MainActor
class ViewModel: Observable {
    var data: [Item] = []  // Already main-actor isolated
}
```

**SwiftUI View Performance:**
```swift
// Use Equatable conformance for complex views
struct ExpensiveRow: View, Equatable {
    let item: Item
    
    static func == (lhs: Self, rhs: Self) -> Bool {
        lhs.item.id == rhs.item.id && lhs.item.updatedAt == rhs.item.updatedAt
    }
    
    var body: some View { ... }
}
```
