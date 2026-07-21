---
name: swift-anti-pattern-guard
description: Use when reviewing Swift code for outdated patterns, modernizing a project, running architecture health checks, or grepping for ObservableObject, DispatchQueue.main, NavigationView, or Core Data.
---

# Swift Anti-Pattern Guard

Detect and replace the highest-impact forbidden patterns. Advisory unless hooks already block them.

## Non-negotiables

| ALWAYS | NEVER |
|--------|--------|
| Report file + pattern + replacement | Auto-rewrite entire modules without review |
| Align with repository guidance and deployment targets | Treat “legacy file” as a permanent exemption without explanation |

## Patterns (phase 1)

### 1. Observation family
**Forbidden:** `ObservableObject`, `@Published`, `@StateObject`, `@ObservedObject`, `@EnvironmentObject`
**Replace:** `@Observable` + plain properties; own with `@State` / inject via `@Environment`

### 2. GCD main queue
**Forbidden:** `DispatchQueue.main.async`, `asyncAfter`
**Replace:** `@MainActor`, `await MainActor.run`, `Task { @MainActor in }`

### 3. NavigationView
**Forbidden:** `NavigationView`
**Replace:** `NavigationStack` or `NavigationSplitView`

### 4. Core Data
**Forbidden:** `NSManagedObject`, `@FetchRequest`, `NSPersistentContainer`
**Replace:** SwiftData `@Model`, `@Query`, `ModelContext`

## How to run

1. Grep the path for forbidden tokens.
2. Group findings by file.
3. For each: why it hurts (concurrency, invalidation, maintenance) + modern replacement.
4. Suggest a minimal fix when local; do not drive-by refactor unrelated code.

```bash
rg -n "ObservableObject|@Published|@StateObject|@ObservedObject|DispatchQueue\\.main|NavigationView|NSManagedObject|@FetchRequest" --glob '*.swift' .
```

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "Only one ObservableObject" | In greenfield Observation code, consistency avoids two state models |
| "DispatchQueue is clearer" | `@MainActor` is clearer under Swift 6 |
| "Core Data already works" | New code is SwiftData; migrate when touching area |

## Pre-finish checklist

- [ ] Grep run on target path
- [ ] Findings include replacement
- [ ] No silent ignore of matches without reason
