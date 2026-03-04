#!/usr/bin/env python3
"""UserPromptSubmit hook - inject voice summary reminder into each turn."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from voice_common import (
    get_voice_config,
    build_full_reminder,
    clear_just_disabled_flag,
)
from terminal_status import update_status, generate_working_title


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"decision": "approve"}))
        return

    # Terminal status: set WORKING pane title (Mercury LLM generates title)
    session_id = data.get("session_id", "")
    prompt = data.get("prompt", "")
    cwd = data.get("cwd", "")
    summary = generate_working_title(prompt) if prompt else ""
    update_status(session_id, "WORKING...", summary=summary, cwd=cwd)

    enabled, _voice, custom_prompt, just_disabled, _notifications = get_voice_config()

    if just_disabled:
        clear_just_disabled_flag()
        print(json.dumps({
            "decision": "approve",
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": (
                    "Voice feedback has been DISABLED. "
                    "Do NOT add 📢 spoken summaries to your responses."
                )
            }
        }))
        return

    if not enabled:
        print(json.dumps({"decision": "approve"}))
        return

    reminder = build_full_reminder(custom_prompt)

    print(json.dumps({
        "decision": "approve",
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": reminder
        }
    }))


if __name__ == "__main__":
    main()
