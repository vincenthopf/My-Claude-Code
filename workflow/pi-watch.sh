#!/bin/bash
# pi-watch.sh — Run pi with live progress output
# Usage: bash ~/.claude/pi-watch.sh [all normal pi arguments]
# Example: bash ~/.claude/pi-watch.sh -p --no-session --provider openai-codex --model gpt-5.4 --thinking high --tools read,write,grep,find,ls "Your prompt here"

pi "$@" --mode json 2>/dev/null | jq -r --unbuffered '
  if .type == "turn_start" then "\n--- Turn \(input_line_number // "") ---"
  elif .type == "message_update" then
    if .assistantMessageEvent.type == "toolcall_end" then
      .assistantMessageEvent.toolCall | "  tool: \(.name) \(.arguments.path // .arguments.file_path // .arguments.command // "" | tostring | .[0:100])"
    elif .assistantMessageEvent.type == "text_start" then "  responding..."
    else empty
    end
  elif .type == "turn_end" then
    .message.usage | "  done: \(.totalTokens) tokens | $\(.cost.total)"
  elif .type == "agent_end" then
    "=== Complete ==="
  else empty
  end
'
