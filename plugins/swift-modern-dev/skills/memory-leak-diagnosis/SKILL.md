---
name: memory-leak-diagnosis
description: Detecting and fixing memory leaks and retain cycles in Swift apps using Instruments, strict concurrency, and @Observable patterns.
---

# Memory Leak Diagnosis

## Common Leak Patterns

### 1. Closure Retain Cycles
```swift
// LEAK: strong self capture in stored closure
class ViewModel {
    var onUpdate: (() -> Void)?
    
    func setup() {
        onUpdate = {
            self.refresh()  // Retain cycle!
        }
    }
}

// FIX: weak capture
func setup() {
    onUpdate = { [weak self] in
        self?.refresh()
    }
}
```

### 2. Delegate Retain Cycles
```swift
// LEAK: strong delegate reference
class Manager {
    var delegate: ManagerDelegate?  // Strong!
}

// FIX: weak delegate
class Manager {
    weak var delegate: ManagerDelegate?
}
```

### 3. Timer Retain Cycles
```swift
// LEAK: Timer retains target strongly
Timer.scheduledTimer(timeInterval: 1, target: self, ...)

// FIX: Use Task-based approach
Task {
    while !Task.isCancelled {
        try await Task.sleep(for: .seconds(1))
        await update()
    }
}
```

### 4. NotificationCenter (pre-iOS 17)
```swift
// LEAK potential: observer not removed
NotificationCenter.default.addObserver(self, ...)

// FIX: Use async sequence (iOS 17+)
for await _ in NotificationCenter.default.notifications(named: .didUpdate) {
    await handleUpdate()
}
```

## Diagnosis with Instruments

1. **Leaks**: Profile > Leaks template > Run through key flows > Check for red leak indicators
2. **Allocations**: Track allocation growth over repeated operations (steady growth = leak)
3. **Memory Graph**: Xcode Debug > Debug Memory Graph > Look for retain cycles (arrows forming loops)

## @Observable Benefits

The `@Observable` macro eliminates many common leak patterns:
- No `@Published` property wrappers (which used Combine under the hood)
- No `sink` subscriptions to leak
- No `AnyCancellable` sets to manage
- Automatic observation tracking with no manual subscription management
