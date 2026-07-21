# Swift anti-patterns (quick catalog)

| Forbidden | Replace with |
|-----------|----------------|
| `ObservableObject`, `@Published`, `@StateObject`, `@ObservedObject`, `@EnvironmentObject` | `@Observable`, `@State`, `@Environment` |
| `DispatchQueue.main.async` / `asyncAfter` | `@MainActor`, `Task { @MainActor in }`, `Task.sleep(for:)` |
| `NavigationView`, `NavigationLink(destination:)` | `NavigationStack`, `navigationDestination(for:)` |
| Core Data (`NSManagedObject`, `@FetchRequest`, `NSPersistentContainer`) | SwiftData `@Model`, `@Query`, `ModelContext` |
| Completion-handler APIs when async exists | `async throws` |
| XCTest for new tests | Swift Testing `@Test`, `#expect` |
