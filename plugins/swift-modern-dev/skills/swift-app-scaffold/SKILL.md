---
name: swift-app-scaffold
description: Use when starting a new iOS or macOS app, bootstrapping Package.swift, or scaffolding a modern SwiftUI architecture with Observation, SwiftData, NavigationStack, and Swift Testing.
---

# Swift App Scaffold

New test files, test targets requiring new files, and test-only helpers/fixtures require explicit user authorization. A request to implement, fix, test, or verify does not by itself authorize their creation. Prefer existing tests and direct runtime checks; ask only when a specific new test has concrete benefit. Run checks appropriate to the change and repeat only after relevant changes, failures, or unresolved concerns.

Bootstrap a modern SwiftUI app without assuming a proprietary shared package, fixed workspace path, or organization-specific module layout.

## Defaults for greenfield apps

| Prefer | Avoid |
|--------|-------|
| Deployment targets chosen from product requirements | Raising targets without confirming supported devices |
| `@Observable` + `NavigationStack` | `ObservableObject` / `NavigationView` in new code |
| SwiftData when it fits the persistence model | Adding persistence before the data model requires it |
| Swift Testing when new unit tests are authorized | Creating new test files without authorization |
| Explicit, reviewed package dependencies | Adding a shared package only for convenience |

Respect an existing repository's architecture and dependency policy when adding a target to an established codebase.

## Package foundation

```swift
// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "YourApp",
    platforms: [
        .iOS(.v18),
        .macOS(.v15),
    ],
    products: [
        .library(name: "YourAppFeature", targets: ["YourAppFeature"]),
    ],
    dependencies: [
        // Add only reviewed dependencies required by the product.
    ],
    targets: [
        .target(name: "YourAppFeature"),
        // Add a test target only when its new test files are explicitly authorized.
    ]
)
```

Adjust tools and platform versions to the installed toolchain and product support policy. Pin dependencies according to the repository's supply-chain rules.

## App entry

```swift
import SwiftUI

@main
struct YourApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
```

Add a SwiftData container only when the app has persistent models:

```swift
import SwiftData

WindowGroup {
    ContentView()
}
.modelContainer(for: [Item.self])
```

## Suggested structure

```text
YourApp/
├── App/
├── Features/
├── Models/
├── Services/
└── Resources/
YourAppTests/
```

Adapt the structure to the product. Prefer feature boundaries over catch-all utility folders as the app grows.

## Checklist

- [ ] Deployment targets match product requirements
- [ ] Dependencies are necessary, reviewed, and version-pinned per repository policy
- [ ] App entry and navigation compile
- [ ] View state uses Observation where appropriate
- [ ] Persistence is added only when required
- [ ] If new tests were authorized, the target includes a meaningful behavior test; otherwise use existing checks or direct runtime verification
- [ ] Accessibility identifiers and labels are considered from the first screen
- [ ] Appropriate build and existing/authorized tests pass, or limitations are reported
- [ ] Repository guidance documents the chosen architecture

## Pre-finish checklist

- [ ] No organization-specific paths, packages, or credentials were introduced
- [ ] Generated files and dependency locks were reviewed before commit
