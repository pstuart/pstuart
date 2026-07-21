---
name: swift-test-scaffold
description: Use when adding Swift tests, creating test targets, scaffolding ViewModel or service tests, or choosing Swift Testing over XCTest.
---

# Swift Test Scaffold

Generate Swift Testing structure that verifies intent, not only surface behavior.

## Non-negotiables

| ALWAYS | NEVER |
|--------|--------|
| `import Testing` for new tests | New XCTest cases |
| Descriptive `@Test("...")` names | Tests that cannot fail when logic changes |
| Mock at protocol/service boundary | Hit live network in unit tests |
| Cover success + failure paths for logic | Test trivial getters / SwiftUI layout trees |

## Structure

```
Tests/YourAppTests/
├── ViewModels/
├── Services/
├── Models/
└── Mocks/
```

## Core pattern

```swift
import Testing
@testable import YourApp

@Suite("FeatureViewModel")
struct FeatureViewModelTests {
    private func makeSUT(service: MockFeatureService = .init()) -> FeatureViewModel {
        FeatureViewModel(service: service)
    }

    @Test("load populates items on success")
    func loadSuccess() async {
        let service = MockFeatureService()
        service.itemsToReturn = [Item(name: "A")]
        let sut = makeSUT(service: service)
        await sut.loadItems()
        #expect(sut.items.count == 1)
    }

    @Test("load records error on failure")
    func loadFailure() async {
        let service = MockFeatureService()
        service.errorToThrow = TestError.boom
        let sut = makeSUT(service: service)
        await sut.loadItems()
        #expect(sut.error != nil)
    }
}
```

```swift
final class MockFeatureService: FeatureServiceProtocol, @unchecked Sendable {
    var itemsToReturn: [Item] = []
    var errorToThrow: Error?

    func fetchItems() async throws -> [Item] {
        if let errorToThrow { throw errorToThrow }
        return itemsToReturn
    }
}
```

## Decision tree

- Business rule / state machine? → test it
- Type system already enforces? → skip
- UI layout only? → skip unit test; use accessibility/manual

## Quick commands

```bash
swift test
# or Xcode Test
```

## Pre-finish checklist

- [ ] Swift Testing only for new files
- [ ] Mocks for dependencies
- [ ] At least one failure-path test for async logic
