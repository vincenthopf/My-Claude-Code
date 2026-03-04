#!/usr/bin/env python3
"""
Stop hook - update terminal status and speak voice summary.

Flow:
1. Generate completion title via Mercury API (with local fallback)
2. Look for 📢 marker in last_assistant_message
3. If short response (≤25 words), speak directly
4. Last resort: truncate to first sentence or 25 words
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from voice_common import MAX_SPOKEN_WORDS, get_voice_config, detect_project_name, speak
from terminal_status import update_status, generate_done_title

# Flexible limit for explicit summaries (1.5x the strict limit)
FLEXIBLE_LIMIT = int(MAX_SPOKEN_WORDS * 1.5)


def extract_voice_marker(text: str) -> str | None:
    """Extract voice summary from 📢 marker if present."""
    pattern = r'^[ \t]*📢[ \t]*(.+?)[ \t]*$'
    match = re.search(pattern, text, re.MULTILINE)
    if match:
        summary = match.group(1).strip()
        summary = re.sub(r'^\[|\]$', '', summary)
        return summary if summary else None
    return None


def trim_to_words(text: str, max_words: int) -> str:
    """Trim text to max_words, adding ellipsis if truncated."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


def extract_first_sentence(text: str) -> str:
    """Extract the first meaningful sentence from a response."""
    # Strip markdown markers, code blocks, headers
    clean = re.sub(r'```[\s\S]*?```', '', text)
    clean = re.sub(r'^#+\s+', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'^\s*[-*]\s+', '', clean, flags=re.MULTILINE)
    clean = clean.strip()

    # Find first sentence ending with . ! or ?
    match = re.match(r'(.+?[.!?])(?:\s|$)', clean, re.DOTALL)
    if match:
        sentence = match.group(1).strip()
        if len(sentence.split()) <= FLEXIBLE_LIMIT:
            return sentence

    return trim_to_words(clean, MAX_SPOKEN_WORDS)


def is_short_response(text: str) -> bool:
    """Check if response is short enough to speak directly."""
    return len(text.split()) <= MAX_SPOKEN_WORDS


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"decision": "approve"}))
        return

    session_id = data.get("session_id", "")
    last_assistant_msg = data.get("last_assistant_message", "")
    cwd = data.get("cwd", "")

    # Terminal status: summarize what was completed via Mercury LLM
    if last_assistant_msg:
        title_summary = generate_done_title(last_assistant_msg)
        update_status(session_id, "DONE", summary=title_summary, cwd=cwd)
    else:
        update_status(session_id, "DONE", cwd=cwd)

    if data.get("stop_hook_active", False):
        print(json.dumps({"decision": "approve"}))
        return

    enabled, voice, _custom_prompt, _just_disabled, notifications = get_voice_config()
    if not enabled or not last_assistant_msg:
        print(json.dumps({"decision": "approve"}))
        return

    project = detect_project_name(cwd) if cwd else ""

    summary = None

    # Strategy 1: Extract 📢 marker (instant)
    marker_summary = extract_voice_marker(last_assistant_msg)
    if marker_summary:
        summary = trim_to_words(marker_summary, FLEXIBLE_LIMIT)

    # Strategy 2: Short response — speak directly
    if not summary and is_short_response(last_assistant_msg):
        summary = last_assistant_msg

    # Strategy 3: Extract first sentence (instant)
    if not summary:
        summary = extract_first_sentence(last_assistant_msg)

    speak(summary, voice, session_id=session_id, project=project, cwd=cwd, notifications=notifications)

    print(json.dumps({"decision": "approve"}))


if __name__ == "__main__":
    main()
