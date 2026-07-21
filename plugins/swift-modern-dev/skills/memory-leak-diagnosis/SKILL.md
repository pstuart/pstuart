---
name: memory-leak-diagnosis
description: Use when investigating memory growth, retain cycles, leaks in Instruments, Task cancellation issues, or ARC problems in Swift 6 apps.
---

# Memory Leak Diagnosis

Find and fix leaks and retain cycles using modern concurrency patterns.

## Non-negotiables

| ALWAYS | NEVER |
|--------|--------|
| Cancel long-lived `Task`s | Infinite `Task` loops without cancellation |
| Prefer structured async over stored escaping closures | Strong `self` in stored closures without reason |
| Profile with Instruments / Memory Graph | “Optimize” without evidence of a leak |
| Prefer `@Observable` + async over Combine sinks | Ignore purple leak markers in Memory Graph |

## Decision tree

- Growth while navigating? → Memory Graph + Leaks instrument
- Closure / delegate cycle? → `weak` / remove stored closures / use async
- Background work outlives UI? → store `Task`, cancel in `deinit` / `.onDisappear` / `.task` lifecycle
- Shared mutable state? → `actor`

## Core fixes

```swift
@Observable
final class SafeViewModel {
    private var workTask: Task<Void, Never>?

    func start() {
        workTask?.cancel()
        workTask = Task {
            while !Task.isCancelled {
                await doWork()
                try? await Task.sleep(for: .seconds(1))
            }
        }
    }

    func stop() {
        workTask?.cancel()
        workTask = nil
    }

    deinit { workTask?.cancel() }
}
```

```swift
// Prefer .task for automatic cancellation with view lifetime
.task {
    await viewModel.load()
}
```

## Instruments quick path

1. Product → Profile → Leaks (or Allocations)
2. Exercise suspect flows
3. Inspect Cycles & Roots
4. Confirm fix with Memory Graph (no abandoned graphs)

## Common leak sources

| Pattern | Fix |
|---------|-----|
| Uncancelled `Task` | Cancel + check `Task.isCancelled` |
| Stored closure capturing self | `weak self` or async API |
| NotificationCenter observer | `AsyncSequence` notifications + cancel |
| Timer | invalidate / use async loop with cancel |

## Pre-finish checklist

- [ ] Root cause identified (not guessed)
- [ ] Cancellation/ownership fixed
- [ ] Re-profiled or Memory Graph clean for the flow
