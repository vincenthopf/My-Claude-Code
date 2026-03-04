#!/usr/bin/env python3
"""Terminal status — sets iTerm2 per-pane title via AppleScript.

Uses osascript to communicate with iTerm2 via Apple Events. Generates
quality titles via Inception Labs Mercury API (1000+ tok/sec diffusion LLM).
"""

import json
import os
import re
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

STATE_DIR = Path.home() / ".claude" / "terminal_status"

MERCURY_API_URL = "https://api.inceptionlabs.ai/v1/chat/completions"
MERCURY_MODEL = "mercury-2"


def _get_mercury_key() -> str | None:
    """Get Mercury API key from env or config file."""
    key = os.environ.get("INCEPTION_API_KEY") or os.environ.get("MERCURY_API_KEY")
    if key:
        return key
    key_file = Path.home() / ".claude" / "inception_api_key"
    if key_file.exists():
        return key_file.read_text().strip()
    return None


def _generate_title(text: str, instruction: str) -> str | None:
    """Call Mercury-2 API to generate a concise title. Returns None on failure."""
    api_key = _get_mercury_key()
    if not api_key:
        return None

    truncated = text[:300]
    prompt = f"{instruction}\n\nText: {truncated}"

    payload = json.dumps({
        "model": MERCURY_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.5,
        "reasoning_effort": "instant",
    }).encode("utf-8")

    req = urllib.request.Request(
        MERCURY_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            title = data["choices"][0]["message"]["content"].strip()
            title = title.strip('"\'').strip()
            # Take first line only, cap length
            title = title.split("\n")[0].strip()
            if len(title) > 50:
                title = title[:50]
            return title if title else None
    except Exception:
        return None


def generate_working_title(prompt: str) -> str:
    """Generate a quality title from a user prompt via Mercury, with fallback."""
    title = _generate_title(
        prompt,
        "Generate a 4-6 word action title for this task. "
        "Format: Action: Subject. Examples: 'Debug: Auth API Flow', "
        "'Build: User Dashboard', 'Fix: Login Bug'. "
        "Reply with ONLY the title, nothing else."
    )
    return title or _extract_summary_fallback(prompt)


def generate_done_title(response: str) -> str:
    """Generate a completion summary from Claude's response via Mercury, with fallback."""
    title = _generate_title(
        response,
        "Summarise what was completed in 4-6 words. "
        "Format: Past Action: Subject. Examples: 'Fixed: Login Bug', "
        "'Built: Dashboard Component', 'Debugged: API Timeout'. "
        "Reply with ONLY the title, nothing else."
    )
    return title or _extract_summary_fallback(response)


def _extract_summary_fallback(text: str, max_words: int = 4) -> str:
    """Fast local fallback: extract keywords when API is unavailable."""
    skip = {
        "the", "a", "an", "to", "and", "or", "in", "on", "at", "is", "it",
        "me", "my", "i", "we", "can", "you", "for", "of", "with", "this",
        "that", "please", "help", "want", "need", "would", "could", "should",
        "like", "just", "also", "some", "make", "do", "be", "have", "has",
    }
    clean = re.sub(r"[^\w\s]", "", text).strip()
    words = clean.split()
    meaningful = [w for w in words if w.lower() not in skip][:max_words]
    if not meaningful:
        meaningful = words[:max_words]
    return " ".join(w.capitalize() for w in meaningful) if meaningful else "Working"


# Keep old name as alias for backward compatibility
extract_summary = _extract_summary_fallback


def _find_tty() -> str | None:
    """Walk up the process tree to find the TTY of our ancestor shell."""
    pid = os.getpid()
    try:
        while pid > 1:
            result = subprocess.run(
                ["ps", "-o", "ppid=,tty=,comm=", "-p", str(pid)],
                capture_output=True, text=True, timeout=2,
            )
            parts = result.stdout.strip().split(None, 2)
            if len(parts) < 2:
                break
            tty = parts[1]
            if tty not in ("??", "-", ""):
                return f"/dev/{tty}"
            pid = int(parts[0])
    except Exception:
        pass
    return None


def _get_tty(session_id: str = "") -> str | None:
    state = _load_state(session_id)
    cached = state.get("tty")
    if cached and Path(cached).exists():
        return cached
    tty = _find_tty()
    if tty:
        _save_state(session_id, tty=tty)
    return tty


def _set_pane_title(tty: str, title: str) -> bool:
    """Set iTerm2 session name by finding the session that owns our TTY."""
    safe_title = title.replace('\\', '\\\\').replace('"', '\\"')
    script = f'''
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if tty of s is "{tty}" then
                    set name of s to "{safe_title}"
                    return "ok"
                end if
            end repeat
        end repeat
    end repeat
end tell
'''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=3,
        )
        return result.stdout.strip() == "ok"
    except Exception:
        return False


def _load_state(session_id: str) -> dict:
    cache_file = STATE_DIR / f"{session_id or 'default'}.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text())
        except Exception:
            pass
    return {}


def _save_state(session_id: str, summary: str = "", tty: str = "") -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = STATE_DIR / f"{session_id or 'default'}.json"
    data = _load_state(session_id)
    if summary:
        data["summary"] = summary
    if tty:
        data["tty"] = tty
    try:
        cache_file.write_text(json.dumps(data))
    except Exception:
        pass


def update_status(
    session_id: str,
    status: str,
    summary: str = "",
    cwd: str = "",
) -> None:
    """Update the pane title bar for this Claude Code session."""
    tty = _get_tty(session_id)
    if not tty:
        return

    if not summary:
        state = _load_state(session_id)
        summary = state.get("summary", "")

    pane_title = f"{status} | {summary}" if summary else status
    _set_pane_title(tty, pane_title)

    if summary:
        _save_state(session_id, summary=summary, tty=tty)
