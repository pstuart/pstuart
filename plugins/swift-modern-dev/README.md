# swift-modern-dev

Modern Swift/iOS development toolkit for [Claude Code](https://claude.ai/code).

Enforces Swift 6 patterns, blocks deprecated APIs, and provides architecture guidance.

## Install

```bash
/plugin marketplace add pstuart/pstuart
/plugin install swift-modern-dev@pstuart
```

## What It Does

### Anti-Pattern Guard (Hook)

Blocks deprecated Swift/SwiftUI patterns before they're written:

| Blocked Pattern | Replacement |
|----------------|-------------|
| `ObservableObject` | `@Observable` macro |
| `@Published` | Direct properties on `@Observable` |
| `@StateObject` | `@State` with `@Observable` |
| `@ObservedObject` | Direct property or `@Environment` |
| `@EnvironmentObject` | `@Environment(Type.self)` |
| `DispatchQueue.main` | `@MainActor` / `MainActor.run` |
| `NavigationView` | `NavigationStack` / `NavigationSplitView` |

### Auto-Format (Hook)

Runs `swiftlint --fix` after every Swift file edit.

### xcbeautify (Hook)

Pipes `xcodebuild` output through `xcbeautify` for cleaner build logs.

### Skills

| Skill | Description |
|-------|-------------|
| Swift Modern Architecture | MVVM + @Observable + SwiftData + NavigationStack patterns |
| Swift Anti-Pattern Guard | Finds outdated Observation, GCD, navigation, and persistence patterns |
| Swift App Scaffold | Dependency-neutral SwiftUI project and package scaffolding |
| Swift Performance Optimization | Instruments profiling, memory, rendering |
| Swift Test Scaffold | Swift Testing framework boilerplate generation |
| Memory Leak Diagnosis | Retain cycle detection and fixes |
| iOS Accessibility | VoiceOver, Dynamic Type, HIG compliance |

### Commands

| Command | Description |
|---------|-------------|
| `/package-dmg` | Build, sign, notarize, package macOS apps into DMGs |

## Requirements

- [jq](https://jqlang.org/) -- for hook JSON processing
- [swiftlint](https://github.com/realm/SwiftLint) -- for auto-formatting
- [xcbeautify](https://github.com/cpisciotta/xcbeautify) -- for clean build output
- [create-dmg](https://github.com/create-dmg/create-dmg) -- for /package-dmg command

## License

MIT
