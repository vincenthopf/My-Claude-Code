#!/usr/bin/env python3
"""Shared voice plugin utilities and constants."""

import json
import re
import subprocess
from pathlib import Path

# Word limit for short response detection and fallback truncation.
# Does NOT apply to explicitly generated summaries (📢 marker or headless Claude).
MAX_SPOKEN_WORDS = 25


def detect_project_name(cwd: str) -> str:
    """Detect a human-readable project name from the working directory.

    Checks pyproject.toml, package.json, Cargo.toml for a project name.
    Falls back to the last meaningful directory component.
    """
    cwd_path = Path(cwd)

    # Check pyproject.toml
    pyproject = cwd_path / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            match = re.search(r'^\s*name\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
            if match:
                return match.group(1)
        except Exception:
            pass

    # Check package.json
    pkg_json = cwd_path / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text())
            name = data.get("name", "")
            if name:
                return name
        except Exception:
            pass

    # Check Cargo.toml
    cargo = cwd_path / "Cargo.toml"
    if cargo.exists():
        try:
            content = cargo.read_text()
            match = re.search(r'^\s*name\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
            if match:
                return match.group(1)
        except Exception:
            pass

    # Fall back to directory name
    return cwd_path.name


def get_voice_config() -> tuple[bool, str, str, bool, bool]:
    """Read voice config from ~/.claude/voice.local.md

    Returns:
        Tuple of (enabled, voice, custom_prompt, just_disabled, notifications)
    """
    config_file = Path.home() / ".claude" / "voice.local.md"

    if not config_file.exists():
        return True, "en-AU-WilliamNeural", "", False, True

    try:
        content = config_file.read_text()
    except OSError:
        return True, "en-AU-WilliamNeural", "", False, True

    enabled = True
    voice = "en-AU-WilliamNeural"
    custom_prompt = ""
    just_disabled = False
    notifications = True

    lines = content.split("\n")
    in_frontmatter = False
    for line in lines:
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                break
        if in_frontmatter:
            if line.startswith("enabled:"):
                val = line.split(":", 1)[1].strip()
                enabled = val.lower() != "false"
            elif line.startswith("voice:"):
                voice = line.split(":", 1)[1].strip()
            elif line.startswith("notifications:"):
                val = line.split(":", 1)[1].strip()
                notifications = val.lower() != "false"
            elif line.startswith("prompt:"):
                val = line.split(":", 1)[1].strip()
                if (val.startswith('"') and val.endswith('"')) or \
                   (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                custom_prompt = val
            elif line.startswith("just_disabled:"):
                val = line.split(":", 1)[1].strip()
                just_disabled = val.lower() == "true"

    return enabled, voice, custom_prompt, just_disabled, notifications


def clear_just_disabled_flag() -> None:
    """Remove the just_disabled flag from config file."""
    config_file = Path.home() / ".claude" / "voice.local.md"

    if not config_file.exists():
        return

    try:
        content = config_file.read_text()
    except OSError:
        return

    lines = content.split("\n")
    new_lines = []
    in_frontmatter = False

    for line in lines:
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            new_lines.append(line)
            continue
        if in_frontmatter and line.startswith("just_disabled:"):
            continue
        new_lines.append(line)

    try:
        config_file.write_text("\n".join(new_lines))
    except OSError:
        return


def build_full_reminder(custom_prompt: str = "") -> str:
    """Build the voice style reminder for UserPromptSubmit hook."""
    reminder = (
        "Voice feedback is enabled. Your responses will be spoken aloud "
        "as a notification. Write naturally — do NOT add any special markers "
        "or summaries. Just keep your final sentence concise and actionable "
        "so it sounds good when spoken."
    )

    if custom_prompt:
        reminder += f"\n\nCUSTOM VOICE INSTRUCTION: {custom_prompt}"

    return reminder


def speak(message: str, voice: str, session_id: str = "",
          project: str = "", cwd: str = "", notifications: bool = True) -> None:
    """Shared function to call the say script for TTS."""
    say_script = Path(__file__).parent.parent / "scripts" / "say"
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
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass
