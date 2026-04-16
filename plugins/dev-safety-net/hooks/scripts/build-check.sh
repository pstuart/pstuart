#!/bin/bash
# Build Check — verifies project builds before session ends

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

if ! git -C "$PROJECT_DIR" rev-parse --git-dir &>/dev/null; then
    exit 0
fi

cd "$PROJECT_DIR"

UNCOMMITTED=$(git status --porcelain 2>/dev/null || true)

SWIFT_MODIFIED=false
JS_MODIFIED=false

if echo "$UNCOMMITTED" | grep -qE '\.swift$'; then
    SWIFT_MODIFIED=true
fi

if echo "$UNCOMMITTED" | grep -qE '\.(ts|tsx|js|jsx|vue)$'; then
    JS_MODIFIED=true
fi

if [[ "$SWIFT_MODIFIED" == "false" && "$JS_MODIFIED" == "false" ]]; then
    exit 0
fi

BUILD_CMD=""
LINT_CMD=""

if [[ -f "Package.swift" ]]; then
    BUILD_CMD="swift build"
    if command -v swiftlint &>/dev/null; then
        LINT_CMD="swiftlint lint --quiet"
    fi
elif find . -maxdepth 2 -name "*.xcodeproj" 2>/dev/null | grep -q .; then
    XCODEPROJ=$(find . -maxdepth 2 -name "*.xcodeproj" | head -1)
    SCHEME=$(xcodebuild -project "$XCODEPROJ" -list 2>/dev/null | grep -A 100 "Schemes:" | grep -v "Schemes:" | head -1 | xargs)
    if [[ -n "$SCHEME" ]]; then
        BUILD_CMD="xcodebuild -project $XCODEPROJ -scheme $SCHEME -configuration Debug build CODE_SIGNING_ALLOWED=NO -quiet"
    fi
    if command -v swiftlint &>/dev/null; then
        LINT_CMD="swiftlint lint --quiet"
    fi
fi

if [[ -f "package.json" ]]; then
    if grep -q '"build"' package.json 2>/dev/null; then
        if [[ -f "nuxt.config.ts" ]] || [[ -f "nuxt.config.js" ]]; then
            BUILD_CMD="npm run build"
        elif grep -q '"type-check"' package.json 2>/dev/null; then
            BUILD_CMD="npm run type-check"
        else
            BUILD_CMD="npm run build"
        fi
    fi
    if [[ -f "node_modules/.bin/eslint" ]] || command -v eslint &>/dev/null; then
        LINT_CMD="npx eslint . --max-warnings=0 --quiet"
    fi
fi

if [[ -z "$BUILD_CMD" ]]; then
    exit 0
fi

BUILD_OUTPUT=$($BUILD_CMD 2>&1) || {
    echo "Build failed. Please fix build errors before stopping."
    echo ""
    echo "Command: $BUILD_CMD"
    echo ""
    echo "Output (last 20 lines):"
    echo "$BUILD_OUTPUT" | tail -20
    exit 2
}

if [[ -n "$LINT_CMD" ]]; then
    LINT_OUTPUT=$($LINT_CMD 2>&1) || {
        ERRORS_ONLY=$(echo "$LINT_OUTPUT" | grep -v '\.build/' | grep -E ': error:' | head -10 || true)
        if [[ -n "$ERRORS_ONLY" ]]; then
            echo "Lint errors found. Consider fixing before stopping."
            echo ""
            echo "Errors (first 10):"
            echo "$ERRORS_ONLY"
        fi
    }
fi

exit 0
