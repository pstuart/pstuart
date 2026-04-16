---
name: swift-test-scaffold
description: Generates Swift Testing framework boilerplate for ViewModels, Services, and Models. Use when adding tests to existing code or setting up test targets.
---

# Swift Test Scaffold

Generate test boilerplate using the Swift Testing framework (`@Test`, `@Suite`, `#expect`).

## When to Use

- "Add tests for this ViewModel"
- "Set up test target"
- "Generate test stubs"

## Test Structure

```swift
import Testing
@testable import MyApp

@Suite("FeatureViewModel Tests")
struct FeatureViewModelTests {
    
    // Shared setup
    let sut: FeatureViewModel
    
    init() {
        sut = FeatureViewModel(service: MockService())
    }
    
    @Test("initial state is correct")
    func initialState() {
        #expect(sut.items.isEmpty)
        #expect(!sut.isLoading)
        #expect(sut.errorMessage == nil)
    }
    
    @Test("loads data successfully")
    func loadData() async {
        await sut.load()
        #expect(sut.items.count > 0)
    }
    
    @Test("handles error gracefully")
    func handleError() async {
        let sut = FeatureViewModel(service: FailingMockService())
        await sut.load()
        #expect(sut.errorMessage != nil)
    }
    
    @Test("parameterized test", arguments: ["a", "b", "c"])
    func validateInput(_ input: String) {
        #expect(!input.isEmpty)
    }
}
```

## Mock Pattern

```swift
// Protocol for dependency injection
protocol ServiceProtocol: Sendable {
    func fetch() async throws -> [Item]
}

// Production implementation
struct RealService: ServiceProtocol {
    func fetch() async throws -> [Item] { ... }
}

// Test mock
struct MockService: ServiceProtocol {
    var items: [Item] = [.sample, .sample2]
    func fetch() async throws -> [Item] { items }
}

struct FailingMockService: ServiceProtocol {
    func fetch() async throws -> [Item] {
        throw URLError(.notConnectedToInternet)
    }
}
```

## What to Test

- **ViewModels**: State transitions, async loading, error handling
- **Services**: API response parsing, error mapping, caching logic
- **Models**: Computed properties, validation, Codable conformance
- **Algorithms**: Business logic, calculations, transformations

## What NOT to Test

- SwiftUI view layout (use previews instead)
- Trivial getters/setters
- Framework behavior (trust Apple's code)
- Private implementation details
