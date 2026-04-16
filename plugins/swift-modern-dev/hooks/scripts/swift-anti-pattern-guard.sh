#!/bin/bash
# Swift Anti-Pattern Guard — blocks deprecated Swift/SwiftUI patterns
# PreToolUse hook for Edit|Write

set -euo pipefail

input=$(cat)

tool_name=$(echo "$input" | jq -r '.tool_name // empty')

if [[ "$tool_name" != "Edit" && "$tool_name" != "Write" ]]; then
    exit 0
fi

new_string=$(echo "$input" | jq -r '.tool_input.new_string // .tool_input.content // empty')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

[[ -z "$new_string" ]] && exit 0
[[ -z "$file_path" ]] && exit 0

ext="${file_path##*.}"

# Only check Swift files
if [[ "$ext" != "swift" ]]; then
    exit 0
fi

if echo "$new_string" | grep -qE '\bObservableObject\b'; then
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "reason": "ObservableObject is forbidden. Use @Observable macro instead (Swift 5.9+/iOS 17+).\n\nReplace:\n  class MyModel: ObservableObject { @Published var ... }\nWith:\n  @Observable class MyModel { var ... }"
  },
  "continue": false
}
EOF
    exit 0
fi

if echo "$new_string" | grep -qE '@Published\b'; then
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "reason": "@Published is forbidden. Use @Observable macro instead — properties are automatically observed.\n\nReplace:\n  @Published var name: String\nWith:\n  var name: String  // inside @Observable class"
  },
  "continue": false
}
EOF
    exit 0
fi

if echo "$new_string" | grep -qE 'DispatchQueue\.main'; then
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "reason": "DispatchQueue.main is forbidden. Use Swift Concurrency instead.\n\nReplace:\n  DispatchQueue.main.async { ... }\nWith:\n  await MainActor.run { ... }\n  // or mark the function/class with @MainActor"
  },
  "continue": false
}
EOF
    exit 0
fi

if echo "$new_string" | grep -qE '\bNavigationView\b'; then
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "reason": "NavigationView is deprecated. Use NavigationStack or NavigationSplitView instead (iOS 16+).\n\nReplace:\n  NavigationView { ... }\nWith:\n  NavigationStack { ... }"
  },
  "continue": false
}
EOF
    exit 0
fi

if echo "$new_string" | grep -qE '@StateObject\b'; then
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "reason": "@StateObject is unnecessary with @Observable. Use @State instead.\n\nReplace:\n  @StateObject var viewModel = MyViewModel()\nWith:\n  @State var viewModel = MyViewModel()  // where MyViewModel is @Observable"
  },
  "continue": false
}
EOF
    exit 0
fi

if echo "$new_string" | grep -qE '@ObservedObject\b'; then
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "reason": "@ObservedObject is unnecessary with @Observable. Pass the object directly or use @Environment.\n\nReplace:\n  @ObservedObject var model: MyModel\nWith:\n  var model: MyModel  // where MyModel is @Observable"
  },
  "continue": false
}
EOF
    exit 0
fi

if echo "$new_string" | grep -qE '@EnvironmentObject\b'; then
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "reason": "@EnvironmentObject is deprecated with @Observable. Use @Environment instead.\n\nReplace:\n  @EnvironmentObject var settings: Settings\nWith:\n  @Environment(Settings.self) var settings"
  },
  "continue": false
}
EOF
    exit 0
fi

exit 0
