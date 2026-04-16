---
description: Build, sign, notarize, and package macOS apps into distributable DMGs with branded installer layout
argument: Optional project path (defaults to current directory)
---

# Package DMG

Build, sign, notarize, and create a distributable DMG installer for a macOS app.

## Prerequisites Check

Verify required tools:
```bash
which xcodebuild codesign fileicon create-dmg
xcrun notarytool --version
```

If missing: `create-dmg` via `brew install create-dmg`, `fileicon` via `brew install fileicon`.

## Workflow

1. **Discover project** -- find .xcodeproj, extract scheme, bundle ID, version
2. **Verify signing** -- find Developer ID certificate, check notarization profile
3. **Build release archive** -- xcodebuild archive with Release configuration
4. **Extract branding** -- accent color from Assets.xcassets, app icon
5. **Sign** -- codesign with Developer ID, hardened runtime
6. **Notarize** -- submit to Apple, wait for approval, staple ticket
7. **Generate DMG background** -- gradient from accent color
8. **Create DMG** -- branded installer with app icon and Applications symlink
9. **Set DMG icon** -- apply app icon to the DMG file
10. **Report** -- file size, checksum, location

## Parameters

- `--skip-notarize` -- skip notarization for dev builds
- `--keep-build` -- keep build artifacts after completion
