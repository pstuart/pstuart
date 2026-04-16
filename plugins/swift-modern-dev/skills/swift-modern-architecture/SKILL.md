---
name: swift-modern-architecture
description: Guide for building iOS apps using Swift 6, iOS 17+, SwiftUI, SwiftData, and modern concurrency patterns. Use when writing Swift/iOS code, designing app architecture, or modernizing legacy patterns.
---

# Swift Modern Architecture Guide

## Core Architecture: MVVM with @Observable

Every SwiftUI app should follow this pattern:

### ViewModel Pattern

```swift
import SwiftUI

@Observable
class FeatureViewModel {
    var items: [Item] = []
    var isLoading = false
    var errorMessage: String?

    private let service: ItemService

    init(service: ItemService = .shared) {
        self.service = service
    }

    func loadItems() async {
        isLoading = true
        defer { isLoading = false }

        do {
            items = try await service.fetchItems()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
```

### View Pattern

```swift
struct FeatureView: View {
    @State private var viewModel = FeatureViewModel()

    var body: some View {
        NavigationStack {
            List(viewModel.items) { item in
                ItemRow(item: item)
            }
            .overlay {
                if viewModel.isLoading {
                    ProgressView()
                }
            }
            .task {
                await viewModel.loadItems()
            }
        }
    }
}
```

## Navigation

Always use `NavigationStack` with typed paths:

```swift
@Observable
class Router {
    var path = NavigationPath()

    func navigate(to destination: AppDestination) {
        path.append(destination)
    }

    func popToRoot() {
        path = NavigationPath()
    }
}

enum AppDestination: Hashable {
    case detail(Item)
    case settings
    case profile(User)
}
```

## Data Persistence with SwiftData

```swift
@Model
class Item {
    var name: String
    var createdAt: Date
    var isCompleted: Bool

    init(name: String) {
        self.name = name
        self.createdAt = .now
        self.isCompleted = false
    }
}
```

## Concurrency

All async work uses structured concurrency:

```swift
// Task groups for parallel work
await withTaskGroup(of: Result.self) { group in
    for url in urls {
        group.addTask { await fetch(url) }
    }
    for await result in group {
        process(result)
    }
}

// MainActor for UI updates
@MainActor
func updateUI() {
    // Safe to update UI state here
}

// Actor for thread-safe state
actor DataStore {
    private var cache: [String: Data] = [:]

    func store(_ data: Data, for key: String) {
        cache[key] = data
    }
}
```

## Forbidden Patterns Reference

| Deprecated | Modern Replacement |
|-----------|-------------------|
| `ObservableObject` | `@Observable` macro |
| `@Published` | Direct properties on `@Observable` class |
| `@StateObject` | `@State` with `@Observable` |
| `@ObservedObject` | Pass directly or `@Environment` |
| `@EnvironmentObject` | `@Environment(Type.self)` |
| `DispatchQueue.main` | `@MainActor` or `MainActor.run` |
| `NavigationView` | `NavigationStack` / `NavigationSplitView` |
| `Core Data` | `SwiftData` |
| `XCTest` (new tests) | Swift Testing (`@Test`, `@Suite`, `#expect`) |
| Completion handlers | `async/await` |

## Testing with Swift Testing

```swift
import Testing

@Suite("ItemViewModel Tests")
struct ItemViewModelTests {
    @Test("loads items successfully")
    func loadItems() async {
        let viewModel = ItemViewModel(service: MockItemService())
        await viewModel.loadItems()
        #expect(viewModel.items.count == 3)
        #expect(!viewModel.isLoading)
    }

    @Test("handles errors gracefully")
    func loadItemsError() async {
        let viewModel = ItemViewModel(service: FailingItemService())
        await viewModel.loadItems()
        #expect(viewModel.errorMessage != nil)
    }
}
```
