#!/usr/bin/env python3
"""
Notification hook - speak and notify when Claude needs attention.

Uses instant pattern matching (no API calls) for maximum speed.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from voice_common import get_voice_config, detect_project_name, is_in_voice_call
from terminal_status import update_status

PLUGIN_ROOT = Path(__file__).parent.parent

FALLBACK_MESSAGES = {
    "permission_prompt": "The agent needs your permission.",
    "worker_permission_prompt": "A background agent needs your permission.",
    "idle_prompt": "The agent is idle and waiting for input.",
    "elicitation_dialog": "The agent has a question for you.",
}

# Patterns to extract tool actions from permission prompts
TOOL_PATTERNS = [
    (r"(?i)bash|command|shell|terminal", "run a command"),
    (r"(?i)edit|modify|update|write.*file", "edit a file"),
    (r"(?i)read|view|open|cat", "read a file"),
    (r"(?i)glob|find|search.*file", "search for files"),
    (r"(?i)grep|search.*content", "search file contents"),
    (r"(?i)git\s+push", "push to git"),
    (r"(?i)git\s+commit", "make a git commit"),
    (r"(?i)git", "run a git command"),
    (r"(?i)npm|yarn|pnpm|bun", "run a package manager command"),
    (r"(?i)pip|uv|conda", "install a package"),
    (r"(?i)docker|container", "run a docker command"),
    (r"(?i)curl|fetch|request|api", "make a network request"),
    (r"(?i)delete|remove|rm\b", "delete something"),
    (r"(?i)install", "install something"),
    (r"(?i)test|spec|jest|pytest", "run tests"),
    (r"(?i)build|compile", "run a build"),
    (r"(?i)deploy", "deploy"),
    (r"(?i)agent|subagent|spawn", "spawn an agent"),
]


def extract_tool_detail(notification_type: str, title: str,
                        message: str) -> str:
    """Extract a speakable description using instant pattern matching."""
    text = f"{title} {message}".strip()

    if notification_type in ("permission_prompt", "worker_permission_prompt"):
        prefix = ("A background agent needs permission to"
                  if notification_type == "worker_permission_prompt"
                  else "The agent needs permission to")
        for pattern, action in TOOL_PATTERNS:
            if re.search(pattern, text):
                return f"{prefix} {action}."
        return FALLBACK_MESSAGES[notification_type]

    if notification_type == "elicitation_dialog":
        # Try to extract the actual question
        # Look for question marks or common question patterns
        q_match = re.search(r'["\']([^"\']{5,60}\?)["\']', text)
        if q_match:
            return f"The agent is asking: {q_match.group(1)}"
        q_match = re.search(r'(?:asking|question)[:\s]+(.{5,60}?)(?:\.|$)', text, re.I)
        if q_match:
            return f"The agent is asking {q_match.group(1).strip().rstrip('.')}."
        return FALLBACK_MESSAGES["elicitation_dialog"]

    return FALLBACK_MESSAGES.get(notification_type, "The agent needs attention.")


def speak_notification(project: str, message: str, voice: str,
                       cwd: str = "", notifications: bool = True,
                       session_id: str = "") -> None:
    """Call the say script to speak the notification."""
    say_script = PLUGIN_ROOT / "scripts" / "say"

    args = [str(say_script), "--voice", voice]
    if session_id:
        args.extend(["--session", session_id])
    if project:
        args.extend(["--project", project])
    if cwd:
        args.extend(["--cwd", cwd])
    if not notifications:
        args.append("--no-notify")
    args.append(message)

    try:
        subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        exit(0)

    notification_type = data.get("notification_type", "")
    notification_title = data.get("title", "")
    notification_msg = data.get("message", "")
    cwd = data.get("cwd", "")
    session_id = data.get("session_id", "")

    # Terminal status: always update, regardless of voice config
    text = f"{notification_title} {notification_msg}".strip()
    if notification_type in ("permission_prompt", "worker_permission_prompt"):
        action = "Needs permission"
        for pattern, desc in TOOL_PATTERNS:
            if re.search(pattern, text):
                action = desc.capitalize()
                break
        update_status(session_id, "PERMISSION", summary=action, cwd=cwd)
    elif notification_type == "elicitation_dialog":
        update_status(session_id, "QUESTION", summary="Has a question", cwd=cwd)
    elif notification_type == "idle_prompt":
        pass  # Don't overwrite — keep previous status visible (agents may be running)
    else:
        update_status(session_id, "ATTENTION", cwd=cwd)

    # Voice notification (only if voice enabled)
    enabled, voice, _custom_prompt, _just_disabled, notifications = get_voice_config()
    if not enabled or is_in_voice_call():
        exit(0)

    project = detect_project_name(cwd) if cwd else ""

    spoken = extract_tool_detail(notification_type, notification_title,
                                 notification_msg)
    if not spoken:
        exit(0)

    speak_notification(project, spoken, voice, cwd, notifications, session_id)


if __name__ == "__main__":
    main()
