---
name: swift-modern-architecture
description: Use when writing Swift or SwiftUI code, designing iOS/macOS architecture, modernizing legacy patterns, or choosing ViewModels, SwiftData, navigation, or concurrency APIs.
---

# Swift Modern Architecture

**Baseline:** Swift 6.3, SwiftUI, Observation, SwiftData, and Swift Testing. Confirm deployment targets against the project requirements.

## Non-negotiables

| ALWAYS | NEVER |
|--------|--------|
| `@Observable` ViewModels | `ObservableObject` / `@Published` / `@StateObject` |
| `async/await`, `actor`, `@MainActor` | `DispatchQueue.main` for UI work |
| `NavigationStack` / `NavigationSplitView` | `NavigationView` |
| SwiftData `@Model` / `@Query` | Core Data for new code |
| Swift Testing for new tests | XCTest for new tests |
| Strict concurrency | Completion handlers when async exists |

## Decision tree

- Need state? → `@Observable` + `@State` / `@Environment`
- Shared mutable service? → `actor`
- Persistence? → SwiftData
- Network? → actor API client + async
- Navigation? → `NavigationStack` + typed destinations
- Reusable code across targets? → Extract a focused package or module with a documented API

## Core patterns

```swift
@Observable
final class ItemsViewModel {
    private let service: ItemsService
    private(set) var items: [Item] = []
    private(set) var isLoading = false

    init(service: ItemsService) {
        self.service = service
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }
        items = (try? await service.fetchItems()) ?? []
    }
}

struct ItemsView: View {
    @State private var viewModel: ItemsViewModel

    var body: some View {
        List(viewModel.items) { item in
            Text(item.name)
        }
        .task { await viewModel.load() }
    }
}
```

```swift
actor ItemsService {
    func fetchItems() async throws -> [Item] {
        let (data, _) = try await URLSession.shared.data(from: endpoint)
        return try JSONDecoder().decode([Item].self, from: data)
    }
}
```

## Testing

```swift
import Testing

@Test("loads items")
func loadsItems() async {
    let vm = ItemsViewModel(service: MockItemsService())
    await vm.load()
    #expect(!vm.items.isEmpty)
}
```

## Load next

| When | Read |
|------|------|
| Full anti-pattern catalog | `references/anti-patterns.md` or skill `swift-anti-pattern-guard` |
| New app bootstrap | `swift-app-scaffold` |
| Test boilerplate | `swift-test-scaffold` |
| Reusable cross-target code | Extract a focused package or module |

## Pre-finish checklist

- [ ] No forbidden observation/GCD/navigation/Core Data APIs
- [ ] Deployment targets match the product support policy
- [ ] Services are actors or otherwise Sendable-safe
- [ ] New tests use Swift Testing
